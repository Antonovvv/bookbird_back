# -*- coding:utf-8 -*-
import uuid


def get_hash_name(filename):
    # 获得文件名后缀
    _, _, suffix = filename.rpartition('.')     # 左子串, 分隔符, 右子串
    return '{}.{}'.format(uuid.uuid4().hex, suffix)
