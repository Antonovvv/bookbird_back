# -*- coding:utf-8 -*-
import time
import redis
import logging
from apscheduler.schedulers.background import BackgroundScheduler

pool_book = redis.ConnectionPool(host='localhost', port='6379', db=0)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s-%(levelname)s- %(message)s',
                    filename='../log/schedule.log',
                    filemode='a')
logger = logging.getLogger(__name__)


def new_rank():
    conn_book = redis.Redis(connection_pool=pool_book)
    now = int(time.time())
    today = int(now / (24 * 3600))
    for name in conn_book.zrange('rank_' + str(today), 0, -1):
        current_count = conn_book.zscore('rank_' + str(today), name)
        sub_count = conn_book.zscore('daily_' + str(today - 7), name)
        if sub_count:
            logger.info('淘汰' + str(today - 7) + ':' + name.decode())
            print('淘汰' + str(today - 7) + ':' + name.decode())
            conn_book.zadd('rank_' + str(today + 1), {name: current_count - sub_count})  # 当前榜减去即将淘汰日写入明日榜
        else:
            logger.info('补齐:' + name.decode())
            print('补齐:' + name.decode())
            conn_book.zadd('rank_' + str(today + 1), {name: current_count})  # 当前榜直接写入明日榜


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(new_rank, 'interval', days=1)
    scheduler.start()
    new_rank()
