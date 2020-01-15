# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
import requests
import hashlib

from app import mp_client
from models import Book, Post, User
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
        logger.info(openid)
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
                })
            except Exception:
                pass
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
