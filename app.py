from flask import Flask

from wechatpy.utils import check_signature

from config import *

app = Flask(__name__)


@app.route('/')
def root():
    return 'Not Found'

@app.route('/')


if __name__ == '__main__':
    app.run()
