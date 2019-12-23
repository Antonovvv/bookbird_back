# -*- coding:utf-8 -*-
import uuid
from datetime import datetime

from ext import database as db


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_name = db.Column(db.String(128), nullable=False, unique=True)
    post_time = db.Column(db.DateTime, nullable=False)
    sale_price = db.Column(db.Integer, nullable=False)
    new = db.Column(db.SmallInteger, nullable=False)
    description = db.Column(db.String(1000))

    book_isbn = db.Column(db.String(32), db.ForeignKey('book.isbn'))
    seller_openid = db.Column(db.String(128), db.ForeignKey('user.openid'))

    def __init__(self, filename, new, description):
        self.image_name = self._hash_name(filename)
        self.post_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sale_price = 0
        self.new = new
        self.description = description

    @staticmethod
    def _hash_name(filename):
        # 获得文件名后缀
        # 左边子串, 分隔符, 右边子串
        _, _, suffix = filename.rpartition('.')
        return '{}, {}'.format(uuid.uuid4().hex, suffix)

    @classmethod
    def get_by_book(cls, isbn):
        return cls.query.filter(book_isbn=isbn).all()
