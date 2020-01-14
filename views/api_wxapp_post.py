# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from models import Book, Post, User
from qiniu import Auth
import qiniu.config

import requests

from ext import database as db
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_post', __name__, url_prefix='/api/mp/post')

AK = 'aboRN3j_k6sYgU-JQWJNjecp_wU56tA24c1EN0eQ'
SK = 'TReUVW1XcEkJC3XSGwOkrYZbB6u-uukJQ-frliZM'

q = Auth(AK, SK)
bucket_name = 'bookbird'


@app.route('/', methods=['GET', 'POST', 'PUT'])
def post():
    if request.method == 'POST':
        bookname = request.form['bookName']
        price = request.form['price']
        new = request.form['new']
        description = request.form['description']
        isbn = request.form['ISBN']
        openid = request.form['openid']
        logger.info("post_isbn: {}".format(isbn))

        book_found = Book.get_by_isbn(isbn)
        if not book_found:
            return jsonify({
                'errMsg': 'invalid isbn'
            }), 404
        else:
            post_ = Post(bookname=bookname, price=price, new=new, description=description, isbn=isbn, openid=openid)
            db.session.add(post_)
            db.session.commit()

            key = post_.image_name
            token = q.upload_token(bucket_name, key, 3600)
            return jsonify({
                'token': token,
                'key': key
            })

    return 'else'
