# -*- coding: utf-8 -*-
from flask import Flask, request, abort
from flask_wtf.csrf import CsrfProtect

from wechatpy.client import WeChatClient
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

from werkzeug.utils import import_string

from config import *
from ext import database as db
from ext import logger

app = Flask(__name__)
app.config['SECRET_KEY'] = '0813'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# CsrfProtect(app)
db.init_app(app)

pub_client = WeChatClient(pub_APPID, pub_APPSECRET)
mp_client = WeChatClient(mp_APPID, mp_APPSECRET)

blueprints = [
    'views.api_wxapp_book:app',
    'views.api_wxapp_post:app',
    'views.api_wxapp_user:app',
    'views.api_wxapp_order:app',
    'views.api_admin:app',
    'views.public:app'  # 公众号接口
]
for bp_name in blueprints:
    bp = import_string(bp_name)
    app.register_blueprint(bp)


@app.route('/')
def root():
    return 'Not Found'


if __name__ == '__main__':
    app.run()
