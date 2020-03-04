# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from datetime import timedelta
from wechatpy.pay import WeChatPay

from app import mp_client
from models import Book, Post, User, CartItem, Order
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_order', __name__, url_prefix='/api/mp/order')
pay_client = WeChatPay(appid=mp_APPID, api_key='ffe973955279fb3c93d9d8198a34aec7', mch_id=mch_ID)   # 微信支付client
# order_client = WeChatOrder(mp_client)   # 传入小程序client，生成订单client


@app.route('', methods=['GET', 'POST', 'PUT'])
def order():
    if request.method == 'POST':
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
                        order_ = Order(deadline=deadline, post_id=post_id, buyer=user_found.openid)

                        prepay_data = pay_client.order.create(
                            trade_type='JSAPI', body='不渴鸟BOOKBIRD-书本',
                            notify_url='https://www.bookbird.cn/api/mp/order/notify',
                            total_fee=post_found.sale_price, user_id=user_found.openid,
                            out_trade_no=order_.id, time_start=order_.now, time_expire=order_.now + timedelta(hours=2))
                        # logger.info(prepay_data)
                        logger.info('')
                        params = pay_client.jsapi.get_jsapi_params(prepay_id=prepay_data['prepay_id'])

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
