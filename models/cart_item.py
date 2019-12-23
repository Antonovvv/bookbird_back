# -*- coding:utf-8 -*-
from ext import database as db


class CartItem(db.Model):
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_checked = db.Column(db.Boolean, nullable=False)

    user_openid = db.Column(db.String(128), db.ForeignKey('user.openid'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
