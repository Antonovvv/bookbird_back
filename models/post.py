# -*- coding:utf-8 -*-
import uuid
from datetime import datetime
from sqlalchemy.sql.expression import func

from ext import database as db
from utils import *

bucket_url = 'http://img.bookbird.cn/'


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_name = db.Column(db.String(128), nullable=False)
    image_name = db.Column(db.String(128), nullable=False, unique=True)
    post_time = db.Column(db.DateTime, nullable=False)
    sale_price = db.Column(db.Integer, nullable=False)
    new = db.Column(db.SmallInteger, nullable=False)    # 0为五成,1为七成,2为九成,3为全新
    description = db.Column(db.String(1000))

    book_isbn = db.Column(db.String(32), db.ForeignKey('book.isbn'), nullable=False)
    seller_openid = db.Column(db.String(128), db.ForeignKey('user.openid'), nullable=False)
    book = db.relationship('Book', backref=db.backref('posts'))
    seller = db.relationship('User', backref=db.backref('posts'))

    is_valid = db.Column(db.Boolean, nullable=False)    # 被下架或被下单则为False

    def __init__(self, isbn, openid, bookname='', price=0, new=0, description=''):
        self.book_name = bookname
        self.image_name = uuid.uuid4().hex  # 随机hash值作为图片文件名
        self.post_time = datetime.now()
        self.sale_price = price
        self.new = new
        self.description = description

        self.book_isbn = isbn
        self.seller_openid = openid
        self.is_valid = True

    def get_post_info(self):
        """
        获取该post信息
        :return: {bookName, imageUrl, sale, new, addr, author, publisher}
        """
        return dict(postId=self.id,
                    bookName=self.book_name,
                    imageUrl=bucket_url + self.image_name,
                    postTime=self.post_time.strftime("%Y-%m-%d %H:%M:%S"),
                    sale=self.sale_price,
                    new=self.new,
                    addr=self.seller.address,
                    author=self.book.author,
                    publisher=self.book.publisher,
                    pubdate=self.book.pubdate,
                    originalPrice=self.book.original_price)

    @classmethod
    def get_by_id(cls, post_id):
        return cls.query.filter_by(id=post_id).first()

    @classmethod
    def get_valid_by_id(cls, post_id):
        return cls.query.filter_by(id=post_id, is_valid=True).first()

    @classmethod
    def get_by_isbn(cls, isbn):
        return cls.query.filter_by(book_isbn=isbn).all()

    @classmethod
    def search_by_name(cls, name):
        return cls.query.filter(cls.book_name.like('%' + name + '%')).all() if name else None

    @classmethod
    def get_by_user(cls, openid, count):
        return cls.query.filter_by(seller_openid=openid).order_by(cls.post_time.desc()).limit(count).all()

    @classmethod
    def get_random(cls, count):
        return cls.query.order_by(func.random()).limit(count).all()
