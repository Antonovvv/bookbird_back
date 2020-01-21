# -*- coding:utf-8 -*-
from ext import database as db

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    register_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)
        self.register_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


if __name__ == "__main__":
    db.create_all()
