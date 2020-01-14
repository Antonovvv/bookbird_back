# -*- coding: utf-8 -*-
from flask import Flask, request, abort

from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

from werkzeug.utils import import_string

from config import *
from ext import database as db
from ext import logger

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)

blueprints = [
    'views.api_wxapp_book:app',
    'views.api_wxapp_post:app',
    'views.api_wxapp_user:app'
]
for bp_name in blueprints:
    bp = import_string(bp_name)
    app.register_blueprint(bp)


@app.route('/')
def root():
    return 'Not Found'


# 公众号接口
@app.route('/wx', methods=['GET', 'POST'])
def public():
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    if request.method == 'GET':
        try:
            check_signature(TOKEN, signature, timestamp, nonce)
        except InvalidSignatureException:
            abort(403)
        echo_str = request.args.get('echostr', '')
        return echo_str


if __name__ == '__main__':
    app.run()
