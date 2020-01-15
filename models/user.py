# -*- coding:utf-8 -*-
from ext import database as db


class User(db.Model):
    __tablename__ = 'user'
    openid = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    student_id = db.Column(db.String(16), nullable=False, unique=True)
    dorm = db.Column(db.String(16), nullable=False)
    money_paid = db.Column(db.Integer, nullable=False)
    money_earned = db.Column(db.Integer, nullable=False)

    token = db.Column(db.String(128), unique=True)

    # posts = db.relationship('Post', backref='user', lazy='dynamic')
    # cart_items = db.relationship('CartItem', backref='user')

    def __init__(self, openid, name='无', student_id='none', dorm='none', token=''):
        self.openid = openid
        self.name = name
        self.student_id = student_id
        self.dorm = dorm
        self.money_paid = 0
        self.money_earned = 0
        self.token = token

    @classmethod
    def get_by_openid(cls, openid):
        return cls.query.filter_by(openid=openid).first()
