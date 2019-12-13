# -*- coding: utf-8 -*-
from flask import Flask, request, abort

from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

from config import *

app = Flask(__name__)


@app.route('/')
def root():
    return '这是不渴鸟！'


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
