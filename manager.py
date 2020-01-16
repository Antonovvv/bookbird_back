# -*- coding:utf-8 -*-
from flask import Flask
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from config import DB_URI
from ext import database as db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)
import models.admin, models.user, models.book, models.post, models.cart_item

manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
