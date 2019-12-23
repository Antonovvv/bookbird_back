# -*- coding:utf-8 -*-
from ext import database as db


class Admin(db.Model):
    __tablename__ = 'admin'
    username = db.Column(db.String(128), primary_key=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    sign_up_time = db.Column(db.DateTime, nullable=False)


if __name__ == "__main__":
    db.create_all()
