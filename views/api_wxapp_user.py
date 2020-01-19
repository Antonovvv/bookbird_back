# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
import requests
import hashlib

from app import mp_client
from models import Book, Post, User, CartItem
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_user', __name__, url_prefix='/api/mp/user')


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
                    'token': token
                }), 201
            except Exception:
                logger.info('fail: ' + openid + token)
                return jsonify({
                    'errMsg': 'new user fail'
                }), 500
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
                'token': token
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
                    return jsonify({
                        'errMsg': 'item exists'
                    }), 403
            else:
                return jsonify({
                    'errMsg': 'user not found'
                }), 404
        else:
            return jsonify({
                'errMsg': 'need params'
            }), 404

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
                                         addr=item.post.seller.dorm,
                                         author=item.post.book.author,
                                         publisher=item.post.book.publisher,
                                         pubdate=item.post.book.pubdate,
                                         originalPrice=item.post.book.original_price,
                                         checked=item.is_checked,
                                         valid=item.post.is_valid)
                        cart_list.append(cart_item)

                    return jsonify({
                        'msg': 'request:ok',
                        'cartList': cart_list
                    })
                else:
                    abort(404)
            else:   # token过期(多端登录)或用户不存在(bug)
                return jsonify({
                    'errMsg': 'overdue token'
                }), 403
        else:
            return jsonify({
                'errMsg': 'need token'
            })

    elif request.method == 'DELETE':
        delete_list = request.form['deleteList'].split(',')     # 参数为字符串，拆分得到字符数组，逐个转为int
        # logger.info(delete_list)
        if delete_list:
            # noinspection PyBroadException
            try:
                for item_id in delete_list:
                    cart_item = CartItem.get_by_id(item_id=int(item_id))
                    db.session.delete(cart_item)
                    db.session.commit()
                return jsonify({
                    'msg': 'delete:ok'
                })
            except Exception:
                abort(500)
        else:
            return jsonify({
                'errMsg': 'need id'
            }), 404


@app.route('/', methods=['GET', 'POST', 'PUT'])
def user():
    if request.method == 'POST':
        openid = request.form['openid']
        name = request.form['name']
        student_id = request.form['studentId']
        dorm = request.form['dorm']

        if not User.get_by_openid(openid):
            user_ = User(openid=openid, name=name, student_id=student_id, dorm=dorm)
            db.session.add(user_)
            db.session.commit()

            return jsonify({
                'status': 'new'
            })
        else:
            return jsonify({
                'status': 'exists'
            })

    return 'else'
