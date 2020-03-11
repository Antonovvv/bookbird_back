# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from datetime import timedelta
from wechatpy.pay import WeChatPay
from qiniu import Auth

from app import mp_client
from models import Book, Post, User, CartItem, Order
from ext import database as db
from ext import logger, SQLAlchemyError, InvalidPostException
from utils import *
from config import *

app = Blueprint('api_wxapp_order', __name__, url_prefix='/api/mp/order')
pay_client = WeChatPay(appid=mp_APPID, api_key='ffe973955279fb3c93d9d8198a34aec7', mch_id=mch_ID)   # 微信支付client
# order_client = WeChatOrder(mp_client)   # 传入小程序client，生成订单client

q = Auth(AK, SK)
bucket_name = 'bookbird'
bucket_url = 'http://img.bookbird.cn/'


@app.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
def order():
    if request.method == 'GET':
        token = request.args.get('token', '')
        order_id = request.args.get('orderId', '')

        user_found = User.get_by_token(token)
        if user_found:
            order_found = Order.get_by_id(order_id)
            if order_found:
                post_items = order_found.post_items
                post_info_list = list()
                for item in post_items:
                    post_info = item.post.get_post_info()
                    post_info_list.append(post_info)
                order_info = order_found.get_order_info()

                if order_found.is_effective and order_found.status == 0:    # 有效的待支付订单
                    remain_time = order_found.get_prepay_remain_time()      # 待支付剩余时间
                    if remain_time == 0:        # 待支付已超时
                        # noinspection PyBroadException
                        try:
                            order_found.cancel()    # 关闭订单
                            db.session.commit()
                            order_info['isEffective'] = order_found.is_effective
                        except Exception:
                            return jsonify({'errMsg': 'Cancel order failed'}), 500
                    else:
                        order_info.setdefault('remainTime', remain_time)

                if user_found.openid == order_found.seller_openid:     # 卖方
                    order_info.setdefault('identity', 'seller')
                elif user_found.openid == order_found.buyer_openid:
                    order_info.setdefault('identity', 'buyer')
                else:
                    return jsonify({'errMsg': 'User is not matched with order'}), 403

                return jsonify({
                    'msg': 'Request: ok',
                    'postInfoList': post_info_list,
                    'orderInfo': order_info
                })
            else:
                return jsonify({'errMsg': 'Order Not Found'}), 404
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403
    elif request.method == 'POST':
        token = request.form.get('token', '')
        post_list = request.form.get('postList', '')
        deadline = request.form.get('deadline', '')

        user_found = User.get_by_token(token)
        if user_found:
            if post_list:
                post_list = post_list.split(',')    # 参数为字符串，拆分得到字符数组
                try:
                    order_, order_post_list_ = Order.create_by_prepay(deadline=deadline, post_list=post_list,
                                                                      buyer=user_found.openid, pay_client=pay_client)
                    logger.info('prepay:' + str(order_.id))
                    params = pay_client.jsapi.get_jsapi_params(prepay_id=order_.prepay_id)  # 支付参数

                    db.session.add_all([order_] + order_post_list_)
                    db.session.commit()
                except SQLAlchemyError:
                    return jsonify({'errMsg': 'SQL ERROR'}), 500
                except InvalidPostException:
                    return jsonify({'errMsg': 'Invalid post'}), 400
                else:
                    return jsonify({
                        'msg': 'Order Create: ok',
                        'params': params,
                        'orderId': order_.id
                    }), 201
            else:
                return jsonify({'errMsg': 'Need postId'}), 400
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403
    elif request.method == 'PUT':
        token = request.form.get('token', '')
        order_id = request.form.get('orderId', '')
        action = request.form.get('action', '')

        user_found = User.get_by_token(token)
        if user_found:
            order_found = Order.get_by_id(order_id)
            if order_found and order_found.is_effective:
                if action == 'send' and order_found.status == 1:        # 待配送订单，确认已送达
                    # noinspection PyBroadException
                    try:
                        order_found.status = 2
                        db.session.commit()
                        return jsonify({'msg': 'Request for send confirm: ok'})
                    except Exception:
                        abort(500)
                elif action == 'receive' and order_found.status == 2:   # 待取书订单，确认已取书
                    # noinspection PyBroadException
                    try:
                        order_found.status = 3
                        db.session.commit()
                        return jsonify({'msg': 'Request for receive confirm: ok'})
                    except Exception:
                        abort(500)
                else:
                    return jsonify({'errMsg': 'Order status mismatch with action'}), 400
            else:
                return jsonify({'errMsg': 'Order unavailable'}), 404
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403
    elif request.method == 'DELETE':
        token = request.form.get('token', '')
        order_id = request.form.get('orderId', '')
        order_found = Order.get_by_id(order_id)
        if order_found:
            if token == order_found.buyer.token:    # 暂时只能由买方取消订单
                if order_found.status <= 1 and order_found.is_effective:    # 暂时只能取消待支付和待配送订单
                    # noinspection PyBroadException
                    try:
                        order_found.cancel()
                        db.session.commit()
                        return jsonify({'msg': 'Delete: ok'})
                    except Exception:
                        abort(500)
                else:
                    return jsonify({'errMsg': 'Cancel not allowed'}), 403
            else:
                return jsonify({'errMsg': 'Invalid token'}), 403
        else:
            return jsonify({'errMsg': 'Invalid orderId'}), 404


@app.route('/prepay', methods=['GET'])
def prepay():
    """待支付订单重新发起支付，获取支付参数"""
    if request.method == 'GET':
        token = request.args.get('token', '')
        order_id = request.args.get('orderId', '')

        user_found = User.get_by_token(token)
        if user_found:
            order_found = Order.get_by_id(order_id)
            if order_found and order_found.is_effective and order_found.status == 0:            # 订单有效且处于待支付状态
                params = pay_client.jsapi.get_jsapi_params(prepay_id=order_found.prepay_id)     # 获取支付参数

                return jsonify({
                    'msg': 'Request: ok',
                    'params': params
                })
            else:
                return jsonify({'errMsg': 'Prepay Order Not Found'}), 404
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403


@app.route('/notify', methods=['POST'])
def order_notify():
    """接收微信支付结果异步通知"""
    notify_xml = request.data.decode()
    notify_data = pay_client.parse_payment_result(notify_xml)   # 解析数据并进行签名校验
    paid_order_id = notify_data['out_trade_no']
    paid_fee = notify_data['total_fee']
    logger.info(notify_data)
    logger.info(paid_order_id)

    order_found = Order.get_by_id(paid_order_id)
    if order_found:
        if paid_fee == order_found.total_price:     # 校验返回的订单金额是否与商户侧的订单金额一致
            if order_found.is_effective and order_found.status == 0:    # 订单有效且处于待支付状态
                # noinspection PyBroadException
                try:
                    order_found.status = 1  # 订单状态更新，待配送
                    db.session.commit()
                    return '''<xml>
                                <return_code><![CDATA[SUCCESS]]></return_code>
                                <return_msg><![CDATA[OK]]></return_msg>
                                </xml>'''
                except Exception:
                    abort(500)
            else:
                return 'WrongStatusException', 404
        else:
            return 'WrongSaleException', 404
    else:
        return 'Invalid orderId', 404
