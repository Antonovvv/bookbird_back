# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
import redis
import logging

database = SQLAlchemy()

pool_book = redis.ConnectionPool(host='localhost', port='6379', db=0)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s-%(levelname)s- %(message)s',
                    filename='./log/mp.log',
                    filemode='a')
logger = logging.getLogger(__name__)
