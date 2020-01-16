# -*- coding:utf-8 -*-
from ext import database as db


class CartItem(db.Model):
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_checked = db.Column(db.Boolean, nullable=False)

    user_openid = db.Column(db.String(128), db.ForeignKey('user.openid'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    user = db.relationship('User', backref=db.backref('cart'))
    post = db.relationship('Post', backref=db.backref('cart_items'))

    def __init__(self, openid, post_id):
        self.is_checked = False
        self.user_openid = openid
        self.post_id = post_id

    @classmethod
    def get_by_id(cls, item_id):
        return cls.query.filter_by(id=item_id).first()

    @classmethod
    def get_by_openid(cls, openid):
        return cls.query.filter_by(user_openid=openid).all()
