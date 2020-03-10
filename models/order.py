# -*- coding:utf-8 -*-
import uuid
from datetime import datetime, timedelta
from time import mktime, time
import random

from ext import database as db
from sqlalchemy import or_
from models import Post
from utils import *


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.String(32), primary_key=True)
    deal_time = db.Column(db.DateTime, nullable=False)      # 下单时间
    deadline = db.Column(db.String(32))                     # 送达时限
    status = db.Column(db.SmallInteger, nullable=False)     # 0为已下单/待支付,1为已支付/待送,2为已送/待取,3为完成

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('order'))

    buyer_openid = db.Column(db.String(128), db.ForeignKey('user.openid'), nullable=False)
    buyer = db.relationship('User', backref=db.backref('bought_deals'))

    prepay_id = db.Column(db.String(64))
    prepay_timestamp = db.Column(db.Integer)
    delivery_image_url = db.Column(db.String(128))

    is_effective = db.Column(db.Boolean, nullable=False)    # 取消订单则为False

    def __init__(self, deadline, post_id, buyer):
        self.now = datetime.now()
        self.id = self.now.strftime("%Y%m%d%H%M%S%f") + str(random.randint(1000, 9999))     # 毫秒时间加4位随机数
        self.deal_time = self.now.strftime("%Y-%m-%d %H:%M:%S")
        self.deadline = deadline
        self.status = 0
        self.post_id = post_id
        self.buyer_openid = buyer
        self.is_effective = True

    @classmethod
    def create_by_prepay(cls, deadline, post_in, buyer, pay_client):    # post_in为对应的post
        """
        创建订单的同时发起预支付
        :param deadline: 送达截至时间
        :param post_in: 书本post实例
        :param buyer: 买方openid
        :param pay_client: WeChatPay对象

        :return order数据表对象
        """
        order = cls(deadline, post_in.id, buyer)
        prepay_data = pay_client.order.create(
            trade_type='JSAPI', body='不渴鸟BOOKBIRD-书本',
            notify_url='https://www.bookbird.cn/api/mp/order/notify',
            total_fee=post_in.sale_price, user_id=order.buyer_openid,
            out_trade_no=order.id, time_start=order.now, time_expire=order.now + timedelta(hours=2))
        order.prepay_id = prepay_data['prepay_id']
        order.prepay_timestamp = int(mktime(order.now.timetuple()))
        return order

    def get_prepay_remain_time(self):
        """获取预支付订单剩余支付时间"""
        remain = 900 - int(time()) + self.prepay_timestamp
        return remain if remain > 0 else 0

    def cancel(self):
        """关闭订单事务"""
        self.is_effective = False
        self.post.is_valid = True   # 恢复post

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
