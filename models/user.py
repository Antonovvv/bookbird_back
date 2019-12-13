# -*- coding:utf-8 -*-
from ext import database as db


class User(db.Model):
    __tablename__ = 'User'
    student_number = db.Column(db.String(128), primary_key=True)
    openid = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    campus = db.Column(db.String(128), nullable=False)
    dorm = db.Column(db.String(128), nullable=False)
    books_id = db.Column(db.String(1000))
    paid = db.Column(db.Integer, nullable=False)
    earned = db.Column(db.Integer, nullable=False)
