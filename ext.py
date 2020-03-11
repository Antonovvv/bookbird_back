# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import redis
import logging

database = SQLAlchemy()

pool_book = redis.ConnectionPool(host='localhost', port='6379', db=0)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s-%(levelname)s- %(message)s',
                    filename='./log/mp.log',
                    filemode='a')
logger = logging.getLogger(__name__)


class BirdException(Exception):
    """Generic exception class for BookBird background app"""

    def __init__(self, errmsg):
        """
        :param errmsg: errmsg
        """
        self.errmsg = errmsg

    def __str__(self):
        return 'errmsg: {}'.format(self.errmsg)

    def __repr__(self):
        return '{name}({msg})'.format(name=self.__class__.__name__, msg=self.errmsg)


class InvalidPostException(BirdException):
    """Order Posts exception"""
    def __init__(self, msg):
        super(InvalidPostException, self).__init__(errmsg=msg)
