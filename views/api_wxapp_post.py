# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from models import Book, Post, User
from qiniu import Auth
import redis
import time
import requests

from ext import database as db
from ext import pool_book
from ext import logger
from utils import *
from config import *

app = Blueprint('api_wxapp_post', __name__, url_prefix='/api/mp/post')

conn_book = redis.Redis(connection_pool=pool_book)

AK = 'aboRN3j_k6sYgU-JQWJNjecp_wU56tA24c1EN0eQ'
SK = 'TReUVW1XcEkJC3XSGwOkrYZbB6u-uukJQ-frliZM'
q = Auth(AK, SK)
bucket_name = 'bookbird'


@app.route('', methods=['GET', 'POST', 'PUT'])
def post():
    if request.method == 'POST':
        book_name = request.form['bookName']
        price = request.form['price']
        new = request.form['new']
        description = request.form['description']
        isbn = request.form['ISBN']
        token = request.form['token']
        logger.info("post_isbn: {}".format(isbn))

        user_found = User.get_by_token(token)
        book_found = Book.get_by_isbn(isbn)
        if not book_found:
            return jsonify({
                'errMsg': 'Invalid isbn'
            }), 404
        else:
            now = int(time.time())
            today = int(now / (24 * 3600))
            # noinspection PyBroadException
            try:
                conn_book.zincrby('post_' + str(today), 1, book_name)   # 计入当日上传
                conn_book.zincrby('rank_' + str(today), 1, book_name)   # 计入当日推荐
                current_count = conn_book.zscore('rank_' + str(today), book_name)
                sub_count = conn_book.zscore('post_' + str(today - 7), book_name)  # 7天前的即将淘汰
                if sub_count:
                    conn_book.zadd('rank_' + str(today + 1), {book_name: current_count - sub_count})  # 当前榜减去即将淘汰日写入明日榜
                else:
                    conn_book.zadd('rank_' + str(today + 1), {book_name: current_count})  # 当前榜直接写入明日榜
                post_ = Post(bookname=book_name, price=price, new=new, description=description,
                             isbn=isbn, openid=user_found.openid)
                db.session.add(post_)
                db.session.commit()

                key = post_.image_name
                up_token = q.upload_token(bucket_name, key, 3600)
                return jsonify({
                    'upToken': up_token,
                    'key': key
                }), 201
            except Exception:
                abort(500)
    elif request.method == 'GET':
        book_name = request.args.get('bookName', '')
        posts = Post.search_by_name(book_name)
        # logger.info(posts)

        search_list = list()
        if posts:
            now = int(time.time())
            today = int(now / (24 * 3600))
            search_names = set()
            for item in posts:
                search_names.add(item.book_name)    # 搜索得到的卖单书名，同名不重复计入
                # logger.info(item.book_name)
                search_item = dict(postId=item.id,
                                   bookName=item.book_name,
                                   imageName=item.image_name,
                                   postTime=item.post_time,
                                   sale=item.sale_price,
                                   new=item.new,
                                   addr=item.seller.address,
                                   author=item.book.author,
                                   publisher=item.book.publisher,
                                   pubdate=item.book.pubdate,
                                   originalPrice=item.book.original_price)
                search_list.append(search_item)

            for name in search_names:
                # noinspection PyBroadException
                try:
                    conn_book.zincrby('search_' + str(today), 1, name)  # 计入当日搜索
                    conn_book.zincrby('rank_' + str(today), 1, name)    # 计入当日推荐
                    current_count = conn_book.zscore('rank_' + str(today), name)
                    sub_count = conn_book.zscore('search_' + str(today - 7), name)  # 7天前的即将淘汰
                    if sub_count:
                        conn_book.zadd('rank_' + str(today + 1), {name: current_count - sub_count})  # 当前榜减去即将淘汰日写入明日榜
                    else:
                        conn_book.zadd('rank_' + str(today + 1), {name: current_count})  # 当前榜直接写入明日榜
                except Exception:
                    pass

            return jsonify({
                'msg': 'Request: ok',
                'searchRes': search_list
            })
        else:
            abort(404)
    return 'else'


@app.route('try', methods=['GET'])
def try_search():
    count = request.args.get('count', 0)
    now = int(time.time())
    today = int(now / (24 * 3600))
    top_list = list()
    for book_name in conn_book.zrevrangebyscore('rank_' + str(today), max=999999, min=0, start=0, num=count):
        top_list.append(book_name.decode())
    return jsonify({
        'tryList': top_list
    })
