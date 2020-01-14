# -*- coding:utf-8 -*-
import uuid
from datetime import datetime

from ext import database as db
from utils import *


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_name = db.Column(db.String(128), nullable=False)
    image_name = db.Column(db.String(128), nullable=False, unique=True)
    post_time = db.Column(db.DateTime, nullable=False)
    sale_price = db.Column(db.Integer, nullable=False)
    new = db.Column(db.SmallInteger, nullable=False)
    description = db.Column(db.String(1000))

    book_isbn = db.Column(db.String(32), db.ForeignKey('book.isbn'), nullable=False)
    seller_openid = db.Column(db.String(128), db.ForeignKey('user.openid'), nullable=False)

    def __init__(self, bookname, price, new, description, isbn, openid):
        self.book_name = bookname
        self.image_name = uuid.uuid4().hex  # 随机hash值作为图片文件名
        self.post_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sale_price = price
        self.new = new
        self.description = description
        self.book_isbn = isbn
        self.seller_openid = openid

    @classmethod
    def get_by_isbn(cls, isbn):
        return cls.query.filter_by(book_isbn=isbn).all()