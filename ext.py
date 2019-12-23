# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
import logging

database = SQLAlchemy()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s-%(levelname)s- %(message)s',
                    filename='./log/mp.log',
                    filemode='a')
logger = logging.getLogger(__name__)
