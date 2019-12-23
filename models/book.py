# -*- coding:utf-8 -*-
from ext import database as db


class Book(db.Model):
    __tablename__ = 'book'
    isbn = db.Column(db.String(32), primary_key=True)
    book_name = db.Column(db.String(128), nullable=False)
    image_url = db.Column(db.String(1000))
    author = db.Column(db.String(128))
    publisher = db.Column(db.String(128))
    pubdate = db.Column(db.String(32))
    original_price = db.Column(db.Integer, nullable=False)

    posts = db.relationship('Post', backref='book', lazy='dynamic')

    def __init__(self, isbn, book_name, image_url='', author='', publisher='', pubdate='', original_price='0'):
        self.isbn = isbn
        self.book_name = book_name
        self.image_url = image_url
        self.author = author
        self.publisher = publisher
        self.pubdate = pubdate
        self.original_price = original_price

    @classmethod
    def get_by_isbn(cls, isbn):
        return cls.query.filter_by(isbn=isbn).first()

    @classmethod
    def get_posts(cls, isbn):
        return cls.query.filter_by(isbn=isbn).first().posts
