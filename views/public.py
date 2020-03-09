# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort

from wechatpy.client import WeChatClient
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

from app import pub_client
from config import *

app = Blueprint('public', __name__, url_prefix='/public')


@app.route('', methods=['GET', 'POST'])
def public():
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    if request.method == 'GET':
        try:
            check_signature(TOKEN, signature, timestamp, nonce)
            echo_str = request.args.get('echostr', '')
            return echo_str
        except InvalidSignatureException:
            abort(403)
