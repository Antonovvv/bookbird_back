# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from models import Book, Post, User

import requests

from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_user', __name__, url_prefix='/api/mp/user')


@app.route('/', methods=['GET', 'POST'])
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
