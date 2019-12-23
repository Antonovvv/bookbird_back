# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort
from models import Book, Post, User

import requests

from ext import database as db
from ext import logger
from config import *

app = Blueprint('api_wxapp', __name__, url_prefix='/api/mp')

url_isbn = 'https://douban.uieee.com/v2/book/isbn/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 \
                  (KHTML, like Gecko) Chrome/79.0.3945.88 Mobile Safari/537.36'
}


@app.route('/book/isbn/<isbn>/', methods=['GET'])
def book(isbn):
    book_found = Book.get_by_isbn(isbn)
    if request.method == 'GET':
        if not book_found:
            res = requests.get(url_isbn + isbn, headers=headers)
            if res.status_code == 200:
                res_book = res.json()
                # logger.info(res_book)

                book_name = res_book['title']
                image_url = res_book['image']
                author = res_book['author'][0]
                publisher = res_book['publisher']
                pubdate = res_book['pubdate']
                price = res_book['price']
                logger.info("isbn:{}, name:{}".format(isbn, book_name))

                book_ = Book(isbn, book_name=book_name, image_url=image_url, author=author,
                             publisher=publisher, pubdate=pubdate, original_price=price)

                db.session.add(book_)
                db.session.commit()

                return jsonify({
                    'title': book_name,
                    'image': image_url,
                    'isbn13': isbn,
                    'author': [author],
                    'publisher': publisher,
                    'pubdate': pubdate,
                    'price': price
                })
            else:
                abort(404)
        else:
            logger.info(book_found)
            return jsonify({
                'title': book_found.book_name,
                'image': book_found.image_url,
                'isbn13': book_found.isbn,
                'author': [book_found.author],
                'publisher': book_found.publisher,
                'pubdate': book_found.pubdate,
                'price': book_found.original_price
            })
