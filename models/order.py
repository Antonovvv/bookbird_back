# -*- coding:utf-8 -*-
import uuid
from datetime import datetime

from ext import database as db
from sqlalchemy import or_
from models import Post
from utils import *


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.String(32), primary_key=True)
    deal_time = db.Column(db.DateTime, nullable=False)
    deadline = db.Column(db.String(32))
    status = db.Column(db.SmallInteger, nullable=False)     # 0为已下单/待送，1为已送/待取，2为完成

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('order'))

    buyer_openid = db.Column(db.String(128), db.ForeignKey('user.openid'), nullable=False)
    buyer = db.relationship('User', backref=db.backref('bought_deals'))

    is_effective = db.Column(db.Boolean, nullable=False)

    def __init__(self, deadline, post_id, buyer):
        self.id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.deal_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.deadline = deadline
        self.status = 0
        self.post_id = post_id
        self.buyer_openid = buyer
        self.is_effective = True

    @classmethod
    def get_by_id(cls, order_id):
        return cls.query.filter_by(id=order_id).first()

    @classmethod
    def get_by_post(cls, post_id):
        return cls.query.filter_by(post_id=post_id).first()

    @classmethod
    def get_by_buyer(cls, buyer):
        return cls.query.filter_by(buyer_openid=buyer).order_by(cls.deal_time.desc()).all()

    @classmethod
    def get_by_seller(cls, seller):
        return cls.query.join(Post, Post.id == cls.post_id)\
                        .filter(Post.seller_openid == seller).order_by(cls.deal_time.desc()).all()

    @classmethod
    def get_dynamics(cls, user):
        return cls.query.join(Post, Post.id == cls.post_id)\
                        .filter(or_(Post.seller_openid == user, cls.buyer_openid == user))\
                        .order_by(cls.deal_time.desc()).all()
