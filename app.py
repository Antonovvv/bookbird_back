from flask import Flask

from wechatpy.utils import check_signature

from config import *

app = Flask(__name__)


@app.route('/')
def root():
    return '这是不渴鸟！'


@app.route('/wx')
def public():
    pass


if __name__ == '__main__':
    app.run()
