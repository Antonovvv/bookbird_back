# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from datetime import timedelta
from wechatpy.pay import WeChatPay
from qiniu import Auth

from app import mp_client
from models import Book, Post, User, CartItem, Order
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_order', __name__, url_prefix='/api/mp/order')
pay_client = WeChatPay(appid=mp_APPID, api_key='ffe973955279fb3c93d9d8198a34aec7', mch_id=mch_ID)   # 微信支付client
# order_client = WeChatOrder(mp_client)   # 传入小程序client，生成订单client

AK = 'aboRN3j_k6sYgU-JQWJNjecp_wU56tA24c1EN0eQ'
SK = 'TReUVW1XcEkJC3XSGwOkrYZbB6u-uukJQ-frliZM'
q = Auth(AK, SK)
bucket_name = 'bookbird'
bucket_url = 'http://img.bookbird.cn/'


@app.route('', methods=['GET', 'POST', 'PUT'])
def order():
    if request.method == 'GET':
        token = request.args.get('token', '')
        order_id = request.args.get('orderId', '')

        user_found = User.get_by_token(token)
        if user_found:
            order_found = Order.get_by_id(order_id)
            if order_found and order_found.is_effective:
                post = order_found.post
                post_info = dict(bookName=post.book_name,
                                 imageUrl=bucket_url + post.image_name,
                                 sale=post.sale_price,
                                 new=post.new,
                                 addr=post.seller.address,
                                 author=post.book.author,
                                 publisher=post.book.publisher)
                order_info = dict(orderId=order_found.id,
                                  dealTime=order_found.deal_time,
                                  deadline=order_found.deadline,
                                  status=order_found.status,
                                  deliveryImage=order_found.delivery_image_url)
                if order_found.status == 0:     # 待支付订单
                    params = pay_client.jsapi.get_jsapi_params(prepay_id=order_found.prepay_id)     # 支付参数
                    order_info.setdefault('prepayData', params)

                if user_found.openid == order_found.post.seller_openid:     # 卖方
                    order_info.setdefault('identity', 'seller')
                elif user_found.openid == order_found.buyer_openid:
                    order_info.setdefault('identity', 'buyer')
                else:
                    return jsonify({'errMsg': 'User is not matched with order'}), 403

                return jsonify({
                    'msg': 'Request: ok',
                    'postInfo': post_info,
                    'orderInfo': order_info
                })
            else:
                return jsonify({'errMsg': 'Order Not Found'}), 404
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403
    elif request.method == 'POST':
        token = request.form.get('token', '')
        post_id = request.form.get('postId', '')
        deadline = request.form.get('deadline', '')

        user_found = User.get_by_token(token)
        if user_found:
            if post_id:
                post_found = Post.get_by_id(post_id)
                if post_found and post_found.is_valid:
                    # noinspection PyBroadException
                    try:
                        '''order_ = Order(deadline=deadline, post_id=post_id, buyer=user_found.openid)

                        prepay_data = pay_client.order.create(
                            trade_type='JSAPI', body='不渴鸟BOOKBIRD-书本',
                            notify_url='https://www.bookbird.cn/api/mp/order/notify',
                            total_fee=post_found.sale_price, user_id=user_found.openid,
                            out_trade_no=order_.id, time_start=order_.now, time_expire=order_.now + timedelta(hours=2))
                        logger.info('prepay:' + str(post_found.id))
                        
                        params = pay_client.jsapi.get_jsapi_params(prepay_id=prepay_data['prepay_id'])'''
                        order_ = Order.create_by_prepay(deadline=deadline, post_in=post_found, buyer=user_found.openid,
                                                        pay_client=pay_client)
                        logger.info('prepay:' + str(order_.id))

                        params = pay_client.jsapi.get_jsapi_params(prepay_id=order_.prepay_id)  # 支付参数

                        post_found.is_valid = False

                        db.session.add(order_)
                        db.session.commit()
                        return jsonify({
                            'msg': 'Request: ok',
                            'params': params
                        }), 201
                    except Exception:
                        abort(500)
                else:
                    return jsonify({'errMsg': 'Invalid postId'}), 404
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
            if order_id and action in ['send', 'receive']:
                order_found = Order.get_by_id(order_id)
                if order_found and action == 'send' and order_found.status == 0:
                    # noinspection PyBroadException
                    try:
                        order_found.status = 1
                        db.session.commit()
                        return jsonify({'msg': 'Request for send confirm: ok'})
                    except Exception:
                        abort(500)
                elif order_found and action == 'receive' and order_found.status == 1:
                    # noinspection PyBroadException
                    try:
                        order_found.status = 2
                        db.session.commit()
                        return jsonify({'msg': 'Request for receive confirm: ok'})
                    except Exception:
                        abort(500)
                else:
                    return jsonify({'errMsg': 'Order status mismatched'}), 404
            else:
                return jsonify({'errMsg': 'Bad Params'}), 400
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403


@app.route('/notify')
def order_notify():
    logger.info(request.args)
    return jsonify({
        'return_code': 'SUCCESS',
        'return_msg': 'OK'
    })
