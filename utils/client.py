# _*_ coding:utf-8 _*_
# @File  : client.py
# @Time  : 2020-08-31 9:08
# @Author: zizle
import re
from PyQt5.QtCore import QProcess
from settings import logger


def get_client_uuid():
    p = QProcess()
    p.start("wmic csproduct get UUID")
    p.waitForFinished()
    result = p.readAllStandardOutput().data().decode('utf-8')
    result_list = re.split(r'\s+', result)
    if len(result_list[1]) != 36:  # 获取uuid失败
        logger.error("Get Client UUID failed!")
        return None
    return result_list[1]
