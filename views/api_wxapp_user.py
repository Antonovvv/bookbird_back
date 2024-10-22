# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
import requests
import hashlib
from qiniu import Auth

from app import mp_client
from models import Book, Post, User, CartItem, Order
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_user', __name__, url_prefix='/api/mp/user')

q = Auth(AK, SK)
bucket_name = 'bookbird-card'
bucket_url = 'http://imgs.bookbird.cn/'


@app.route('/login', methods=['GET'])
def user_login():
    code = request.args.get('code', '')
    if code:
        session_res = mp_client.wxa.code_to_session(code)
        openid = session_res['openid']
        key = session_res['session_key']
        logger.info('login: ' + openid)
        strs = openid + key
        token = hashlib.md5(strs.encode('utf-8')).hexdigest()   # 合并openid与session_key，MD5加密得到token

        user_found = User.get_by_openid(openid)
        if not user_found:  # 新用户
            # noinspection PyBroadException
            try:
                user_ = User(openid=openid, token=token)    # 新增
                db.session.add(user_)
                db.session.commit()
            except Exception:
                logger.info('fail: ' + openid + token)
                return jsonify({'errMsg': 'Fail to add new user'}), 500
            else:
                return jsonify({
                    'token': token,
                    'isAuthorized': False
                }), 201
        else:
            if token == user_found.token:   # session_key未过期
                pass
            else:
                # noinspection PyBroadException
                try:
                    user_found.token = token    # 替换为新token
                    db.session.commit()
                except Exception:
                    pass
            return jsonify({
                'token': token,
                'isAuthorized': user_found.is_authorized
            })
    else:
        return 'invalid code', 404


@app.route('/posts', methods=['GET', 'DELETE'])
def posts():
    if request.method == 'GET':
        token = request.args.get('token', '')
        count = request.args.get('count', 0)
        if token:
            user_found = User.get_by_token(token)
            if user_found:
                posts = Post.get_by_user(openid=user_found.openid, count=count)
                post_list = list()
                if posts:
                    for item in posts:
                        if item.is_valid:
                            post_item = item.get_post_info()
                            post_list.append(post_item)
                    return jsonify({
                        'msg': 'Request: ok',
                        'postList': post_list
                    })
                else:
                    return jsonify({'msg': 'Request: ok'}), 204
            else:
                return jsonify({'errMsg': 'Overdue token'}), 403
        else:
            return jsonify({'errMsg': 'Need token'}), 400
    elif request.method == 'DELETE':
        token = request.form.get('token', '')
        delete_id = request.form.get('deleteId', '')
        if delete_id:
            post_found = Post.get_by_id(delete_id)
            if token == post_found.seller.token:
                # noinspection PyBroadException
                try:
                    post_found.is_valid = False
                    db.session.commit()
                except Exception:
                    abort(500)
                else:
                    return jsonify({'msg': 'Delete: ok'})
            else:
                return jsonify({'errMsg': 'Invalid token'}), 403
        else:
            return jsonify({'errMsg': 'Need id'}), 400


@app.route('/orders', methods=['GET'])
def order():
    if request.method == 'GET':
        token = request.args.get('token', '')
        order_type = request.args.get('orderType', '')
        user_found = User.get_by_token(token)
        if user_found:
            if order_type == 'bought':
                orders = Order.get_by_buyer(buyer=user_found.openid)
            elif order_type == 'sold':
                orders = Order.get_by_seller(seller=user_found.openid)
            else:
                return jsonify({'errMsg': 'Invalid type'}), 400
            order_list = list()
            if orders:
                for item in orders:
                    order_item = item.get_preview_info(user=user_found.openid)
                    order_list.append(order_item)
                return jsonify({
                    'msg': 'Request: ok',
                    'orderList': order_list
                })
            else:
                return jsonify({'msg': 'Request: ok'}), 204
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403


@app.route('/dynamics', methods=['GET'])
def dynamic():
    token = request.args.get('token', '')
    user_found = User.get_by_token(token)
    if user_found:
        dynamics = Order.get_dynamics(user=user_found.openid)
        dynamic_list = list()
        if dynamics:
            for item in dynamics:
                if item.is_effective:
                    dynamic_item = item.get_preview_info(user=user_found.openid)
                    dynamic_list.append(dynamic_item)
            return jsonify({
                'msg': 'Request: ok',
                'dynamicList': dynamic_list
            })
        else:
            return jsonify({'msg': 'Request: ok'}), 204
    else:
        return jsonify({'errMsg': 'Invalid token'}), 403


@app.route('/cart', methods=['GET', 'POST', 'DELETE'])
def cart():
    if request.method == 'POST':
        token = request.form.get('token', '')
        post_id = request.form.get('postId', '')
        user_found = User.get_by_token(token)
        if user_found:
            post_found = Post.get_valid_by_id(post_id)
            if post_found:
                if int(post_id) not in [item.post_id for item in user_found.cart]:
                    """接收参数post_id为字符串，sql查询时会自动转为数字，但在比较时需要转为数字"""
                    # noinspection PyBroadException
                    try:
                        cart_item_ = CartItem(openid=user_found.openid, post_id=post_id)
                        db.session.add(cart_item_)
                        db.session.commit()
                    except Exception:
                        abort(500)
                    else:
                        return jsonify({
                            'cartItemId': cart_item_.id
                        }), 201
                else:
                    return jsonify({'errMsg': 'Item exists'}), 400
            else:
                return jsonify({'errMsg': 'Invalid postId'}), 404
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403

    elif request.method == 'GET':
        token = request.args.get('token', '')
        if token:
            user_found = User.get_by_token(token)
            if user_found:  # 根据token查找到用户
                cart_items = CartItem.get_by_openid(openid=user_found.openid)   # 按添加顺序倒序
                # cart_items = user_found.cart
                cart_list = list()
                if cart_items:
                    for item in cart_items:
                        cart_item = item.get_cart_item_info()
                        cart_list.append(cart_item)

                    return jsonify({
                        'msg': 'Request: ok',
                        'cartList': cart_list
                    })
                else:
                    return jsonify({'msg': 'Request: ok'}), 204
            else:   # token过期(多端登录)或用户不存在(bug)
                return jsonify({'errMsg': 'Overdue token'}), 403
        else:
            return jsonify({'errMsg': 'Need token'}), 400

    elif request.method == 'DELETE':
        token = request.form.get('token', '')
        delete_list = request.form.get('deleteList', '')
        # logger.info(delete_list)
        if delete_list:
            delete_list = delete_list.split(',')    # 参数为字符串，拆分得到字符数组
            # noinspection PyBroadException
            try:
                for item_id in delete_list:
                    cart_item = CartItem.get_by_id(item_id=item_id)
                    if cart_item:
                        if token == cart_item.user.token:
                            db.session.delete(cart_item)
                            db.session.commit()
                        else:
                            return jsonify({'errMsg': 'Invalid token'}), 403
                    else:
                        return jsonify({'errMsg': 'CartItem not found'}), 204
            except Exception:
                abort(500)
            else:
                return jsonify({'msg': 'Delete: ok'})
        else:
            return jsonify({'errMsg': 'Need cart item id'}), 400


@app.route('', methods=['GET', 'PUT'])
def user():
    if request.method == 'PUT':
        token = request.form.get('token')
        name = request.form.get('myName', '')
        student_id = request.form.get('studentId', '')
        address = request.form.get('address', '')

        user_found = User.get_by_token(token)
        if user_found:
            if name and student_id and address:
                card_image_name = uuid.uuid4().hex
                card_image_url = bucket_url + card_image_name
                # noinspection PyBroadException
                try:
                    user_found.name = name
                    user_found.student_id = student_id
                    user_found.address = address
                    user_found.card_image_url = card_image_url
                    user_found.is_authorized = True
                    db.session.commit()

                    up_token = q.upload_token(bucket_name, card_image_name, 3600)
                except Exception:
                    abort(500)
                else:
                    return jsonify({
                        'upToken': up_token,
                        'key': card_image_name
                    })
            else:
                return jsonify({'errMsg': 'Full information required'}), 400
        else:
            return jsonify({'errMsg': 'Overdue token'}), 403
    elif request.method == 'GET':
        token = request.args.get('token', '')
        user_found = User.get_by_token(token)
        if user_found:
            if user_found.is_authorized:
                return jsonify({
                    'myName': user_found.name,
                    'studentId': user_found.student_id,
                    'address': user_found.address,
                    'cardImageUrl': user_found.card_image_url
                })
            else:
                return jsonify({'msg': 'Not authorized'}), 204
        else:
            return jsonify({'errMsg': 'Overdue token'}), 403
