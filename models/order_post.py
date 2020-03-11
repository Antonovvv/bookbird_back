# -*- coding:utf-8 -*-
from ext import database as db


class OrderPost(db.Model):
    """
    订单order与书本post中间关系表
    """
    __tablename__ = "order_post"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(32), db.ForeignKey('order.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    order = db.relationship('Order', backref=db.backref('post_items'))  # order表的反向引用,由order.posts访问order_post列表
    post = db.relationship('Post', backref=db.backref('orders'))        # 关联post表,由order_post.post访问post

    def __init__(self, order_id, post_id):
        self.order_id = order_id
        self.post_id = post_id
