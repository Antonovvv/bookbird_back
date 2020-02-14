# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
import requests
import hashlib
from qiniu import Auth

from app import mp_client
from models import Book, Post, User, CartItem
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_user', __name__, url_prefix='/api/mp/user')

AK = 'aboRN3j_k6sYgU-JQWJNjecp_wU56tA24c1EN0eQ'
SK = 'TReUVW1XcEkJC3XSGwOkrYZbB6u-uukJQ-frliZM'
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
                return jsonify({
                    'token': token,
                    'isAuthorized': False
                }), 201
            except Exception:
                logger.info('fail: ' + openid + token)
                return jsonify({'errMsg': 'Fail to add new user'}), 500
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


@app.route('/cart', methods=['GET', 'POST', 'DELETE'])
def cart():
    if request.method == 'POST':
        token = request.form['token']
        post_id = int(request.form['postId'])
        if token and post_id:
            user_found = User.get_by_token(token)   # 参数为字符，转为int
            if user_found:
                if post_id not in [item.post_id for item in user_found.cart]:
                    # noinspection PyBroadException
                    try:
                        cart_item_ = CartItem(openid=user_found.openid, post_id=post_id)
                        db.session.add(cart_item_)
                        db.session.commit()
                        return jsonify({
                            'cartItemId': cart_item_.id
                        }), 201
                    except Exception:
                        abort(500)
                else:
                    return jsonify({'errMsg': 'Item exists'}), 403
            else:
                return jsonify({'errMsg': 'User not found'}), 404
        else:
            return jsonify({'errMsg': 'Need params'}), 404

    elif request.method == 'GET':
        token = request.args.get('token', '')
        if token:
            user_found = User.get_by_token(token)
            if user_found:  # 根据token查找到用户
                # cart_items = CartItem.get_by_openid(openid=user_found.openid)
                cart_items = user_found.cart
                # logger.info(cart_items)

                cart_list = list()
                if cart_items:
                    for item in cart_items:
                        cart_item = dict(cartItemId=item.id,
                                         bookName=item.post.book_name,
                                         imageName=item.post.image_name,
                                         sale=item.post.sale_price,
                                         new=item.post.new,
                                         addr=item.post.seller.address,
                                         author=item.post.book.author,
                                         publisher=item.post.book.publisher,
                                         pubdate=item.post.book.pubdate,
                                         originalPrice=item.post.book.original_price,
                                         checked=item.is_checked,
                                         valid=item.post.is_valid)
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
            return jsonify({'errMsg': 'Need token'})

    elif request.method == 'DELETE':
        token = request.form.get('token', '')
        delete_list = request.form['deleteList'].split(',')     # 参数为字符串，拆分得到字符数组，逐个转为int
        # logger.info(delete_list)
        if delete_list:
            for item_id in delete_list:
                cart_item = CartItem.get_by_id(item_id=int(item_id))
                if cart_item:
                    if token == cart_item.user.token:
                        # noinspection PyBroadException
                        try:
                            db.session.delete(cart_item)
                            db.session.commit()
                            return jsonify({'msg': 'Delete: ok'})
                        except Exception:
                            abort(500)
                    else:
                        return jsonify({'errMsg': 'Invalid token'}), 403
                else:
                    return jsonify({'errMsg': 'CartItem not found'}), 404
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
                    return jsonify({
                        'upToken': up_token,
                        'key': card_image_name
                    })
                except Exception:
                    abort(500)
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
