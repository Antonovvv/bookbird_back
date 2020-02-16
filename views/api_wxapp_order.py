# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort

from app import mp_client
from models import Book, Post, User, CartItem, Order
from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_order', __name__, url_prefix='/api/mp/order')


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
                        post_found.is_valid = False
                        db.session.add(order_)
                        db.session.commit()
                        return jsonify({'msg': 'Request: ok'}), 201
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
