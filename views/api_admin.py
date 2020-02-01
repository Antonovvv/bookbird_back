# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, abort, current_app, session
import logging
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadData
from models import Book, Post, User, Admin, CartItem
from qiniu import Auth

from ext import database as db

from wtforms import Form
from wtforms import StringField, PasswordField
from wtforms.validators import length, DataRequired, EqualTo

app = Blueprint('api_admin', __name__, url_prefix='/api/admin')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s-%(levelname)s- %(message)s',
                    filename='./log/admin.log',
                    filemode='a')
logger = logging.getLogger(__name__)

url_isbn = 'https://douban.uieee.com/v2/book/isbn/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 \
                  (KHTML, like Gecko) Chrome/79.0.3945.88 Mobile Safari/537.36'
}

AK = 'aboRN3j_k6sYgU-JQWJNjecp_wU56tA24c1EN0eQ'
SK = 'TReUVW1XcEkJC3XSGwOkrYZbB6u-uukJQ-frliZM'
q = Auth(AK, SK)
bucket_name = 'bookbird'


class RegistrationForm(Form):
    username = StringField('username', [length(min=6, max=25)])
    password = PasswordField('password', [length(min=8), DataRequired(),
                                          EqualTo('confirm', message='Password must match')])
    confirm = PasswordField('passwordRepeat')


class LoginForm(Form):
    username = StringField('username', [length(min=6, max=25)])
    password = PasswordField('password', [length(min=8), DataRequired()])


def create_token(username):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=1800)
    token = s.dumps({
        'username': username
    }).decode("ascii")
    return token


def verify_token(token):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=1800)
    try:
        data = s.loads(token)
    except BadData:
        return None
    return data['username']


@app.route('/register', methods=['POST'])
def register():
    _username = request.form.get('username', '')
    _password = request.form.get('password', '')
    _confirm = request.form.get('passwordRepeat', '')
    form = RegistrationForm(request.form)
    if request.method == 'POST':
        if form.validate():
            admin_found = Admin.get_by_username(form.username.data)
            if not admin_found:
                # noinspection PyBroadException
                try:
                    admin_ = Admin(username=form.username.data, password=form.password.data)
                    db.session.add(admin_)
                    db.session.commit()
                    return jsonify({
                        'msg': 'Register: ok'
                    }), 201
                except Exception:
                    return jsonify({'errMsg': 'Fail to sign in'}), 500
            else:
                return jsonify({'errMsg': 'Username exists'}), 403
        else:
            if 6 <= len(_username) <= 25 and len(_password) >= 8 and _confirm == _password:
                admin_found = Admin.get_by_username(_username)
                if not admin_found:
                    # noinspection PyBroadException
                    try:
                        admin_ = Admin(username=_username, password=_password)
                        db.session.add(admin_)
                        db.session.commit()
                        return jsonify({
                            'msg': 'Register: ok',
                            'warn': 'Please observe API document'
                        }), 201
                    except Exception:
                        return jsonify({'errMsg': 'Fail to sign in'}), 500
                else:
                    return jsonify({'errMsg': 'Username exists'}), 403
            else:
                return jsonify({'errMsg': 'Bad params'}), 400


@app.route('/login', methods=['POST'])
def login():
    _username = request.form.get('username', '')
    _password = request.form.get('password', '')
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate():
            admin_found = Admin.get_by_username(form.username.data)
            if admin_found and admin_found.verify_password(form.password.data):
                token = create_token(admin_found.username)
                session['token'] = token
                return jsonify({'msg': 'Login: ok'})
            else:
                return jsonify({'errMsg': 'Wrong username or password'}), 403
        else:
            if 6 <= len(_username) <= 25 and len(_password) >= 8:
                admin_found = Admin.get_by_username(_username)
                if admin_found and admin_found.verify_password(_password):
                    token = create_token(admin_found.username)
                    session['token'] = token
                    return jsonify({'msg': 'Login: ok'})
                else:
                    return jsonify({'errMsg': 'Wrong username or password'}), 403
            else:
                return jsonify({'errMsg': 'Invalid username or password'}), 400


@app.route('/book', methods=['GET'])
def book():
    token = session.get('token')
    if not token:
        return jsonify({'errMsg': 'Did not login'}), 403
    else:
        username = verify_token(token)
        if username:
            name = request.args.get('name')
            if name:
                books = Book.search_by_name(name)
                search_list = list()
                if books:
                    for item in books:
                        search_item = dict(isbn=item.isbn,
                                           name=item.book_name,
                                           imageUrl=item.image_url,
                                           author=item.author,
                                           publisher=item.publisher,
                                           pubdate=item.pubdate,
                                           originalPrice=item.original_price)
                        search_list.append(search_item)
                    return jsonify({
                        'msg': 'Request: ok',
                        'bookList': search_list
                    })
                else:
                    abort(404)
            else:
                return jsonify({'errMsg': 'Need params'}), 400
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403


@app.route('/book/isbn/<isbn>', methods=['GET'])
def isbn(isbn):
    pass


@app.route('/user', methods=['GET'])
def user():
    token = session.get('token')
    if token:
        username = verify_token(token)
        if username:
            users = User.get_all()
            user_list = list()
            if users:
                for user in users:
                    if user.is_authorized:
                        item = dict(name=user.name,
                                    studentId=user.student_id,
                                    address=user.address,
                                    cardImageUrl=user.card_image_url,
                                    isAuthorized=user.is_authorized)
                        user_list.append(item)
                return jsonify({
                    'msg': 'Request: ok',
                    'userList': user_list
                })
            else:
                abort(404)
        else:
            return jsonify({'errMsg': 'Invalid token'}), 403
    else:
        return jsonify({'errMsg': 'Did not login'}), 403

