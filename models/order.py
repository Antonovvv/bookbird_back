# -*- coding:utf-8 -*-
# import uuid
from datetime import datetime, timedelta
from time import mktime, time
import random

from ext import database as db
from ext import InvalidPostException
from sqlalchemy import or_
from .post import Post
from .order_post import OrderPost


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.String(32), primary_key=True)
    deal_time = db.Column(db.DateTime, nullable=False)      # 下单时间
    deadline = db.Column(db.String(32))                     # 送达时限
    status = db.Column(db.SmallInteger, nullable=False)     # 0为已下单/待支付,1为已支付/待送,2为已送/待取,3为完成
    total_price = db.Column(db.Integer, nullable=False)     # 总价

    # post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    # post = db.relationship('Post', backref=db.backref('order'))
    seller_openid = db.Column(db.String(128), nullable=False)   # 卖方openid,冗余信息,减少查询量

    buyer_openid = db.Column(db.String(128), db.ForeignKey('user.openid'), nullable=False)
    buyer = db.relationship('User', backref=db.backref('bought_deals'))

    prepay_id = db.Column(db.String(64))
    prepay_timestamp = db.Column(db.Integer)
    delivery_image_url = db.Column(db.String(128))

    is_effective = db.Column(db.Boolean, nullable=False)    # 取消订单则为False

    def __init__(self, deadline, total_price, seller, buyer):
        self.now = datetime.now()
        self.id = self.now.strftime("%Y%m%d%H%M%S%f") + str(random.randint(1000, 9999))     # 毫秒时间加4位随机数
        self.deal_time = self.now
        self.deadline = deadline
        self.status = 0
        self.total_price = total_price
        self.seller_openid = seller
        self.buyer_openid = buyer
        self.is_effective = True

    @classmethod
    def create_by_prepay(cls, deadline, post_list, buyer, pay_client):
        """
        创建订单的同时发起预支付
        :param deadline: 送达截至时间
        :param post_list: 书本post_id列表
        :param buyer: 买方openid
        :param pay_client: WeChatPay对象

        :return order数据表对象, order_post中间表对象列表
        """
        post_0 = Post.get_by_id(post_list[0])   # 以第一项post为基准
        if not post_0:
            raise InvalidPostException('Invalid post in creating order!')
        seller = post_0.seller_openid           # 唯一的卖方openid
        total_price = post_0.sale_price         # post总价

        for post_id in post_list[1:]:           # 剩余的post
            post = Post.get_valid_by_id(post_id)
            if post and post.seller_openid == seller:   # 有效的post且为同一卖方
                total_price += post.sale_price
                post.is_valid = False       # 使post失效
            else:
                raise InvalidPostException('Invalid post in creating order!')

        order = cls(deadline, total_price, seller, buyer)    # 校验通过,创建order
        order_post_list = list()
        for post_id in post_list:
            order_post = OrderPost(order_id=order.id, post_id=post_id)  # 创建order与post中间关系
            order_post_list.append(order_post)

        prepay_data = pay_client.order.create(  # 发起预支付
            trade_type='JSAPI', body='不渴鸟BOOKBIRD-书本', notify_url='https://www.bookbird.cn/api/mp/order/notify',
            total_fee=total_price, user_id=order.buyer_openid, out_trade_no=order.id,
            time_start=order.now, time_expire=order.now + timedelta(hours=2))
        order.prepay_id = prepay_data['prepay_id']
        order.prepay_timestamp = int(mktime(order.now.timetuple()))

        return order, order_post_list

    def get_prepay_remain_time(self):
        """获取预支付订单剩余支付时间"""
        remain = 900 - int(time()) + self.prepay_timestamp
        return remain if remain > 0 else 0

    def cancel(self):
        """关闭订单事务"""
        self.is_effective = False
        for item in self.post_items:
            item.post.is_valid = True   # 恢复post

    def get_order_info(self):
        """获取订单信息"""
        return dict(dealTime=self.deal_time.strftime("%Y-%m-%d %H:%M:%S"),
                    deadline=self.deadline,
                    status=self.status,
                    address=self.post_items[0].post.seller.address,
                    deliveryImage=self.delivery_image_url,
                    isEffective=self.is_effective)

    def get_preview_info(self, user):
        """获取订单卡片预览信息(包括书本部分信息)"""
        return dict(orderId=self.id,
                    orderTime=self.deal_time.strftime("%Y-%m-%d %H:%M:%S"),
                    bookName=self.post_items[0].post.book_name,
                    imageName=self.post_items[0].post.image_name,
                    deadline=self.deadline,
                    address=self.post_items[0].post.seller.address,
                    totalPrice=self.total_price,
                    identity='seller' if user == self.seller_openid else 'buyer',
                    status=self.status)

    @classmethod
    def get_by_id(cls, order_id):
        return cls.query.filter_by(id=order_id).first()

    @classmethod
    def get_by_buyer(cls, buyer):
        return cls.query.filter_by(buyer_openid=buyer).order_by(cls.deal_time.desc()).all()

    @classmethod
    def get_by_seller(cls, seller):
        return cls.query.filter_by(seller_openid=seller).order_by(cls.deal_time.desc()).all()
    '''return cls.query.join(Post, Post.id == cls.post_id)\
        .filter(Post.seller_openid == seller).order_by(cls.deal_time.desc()).all()'''

    @classmethod
    def get_dynamics(cls, user):
        return cls.query.filter(or_(cls.seller_openid == user, cls.buyer_openid == user))\
            .order_by(cls.deal_time.desc()).all()

    '''return cls.query.join(Post, Post.id == cls.post_id)\
        .filter(or_(Post.seller_openid == user, cls.buyer_openid == user))\
        .order_by(cls.deal_time.desc()).all()'''
