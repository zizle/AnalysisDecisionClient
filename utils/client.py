# _*_ coding:utf-8 _*_
# @File  : client.py
# @Time  : 2020-08-31 9:08
# @Author: zizle
import re
import os
from PyQt5.QtCore import QProcess, QSettings
from settings import logger, BASE_DIR


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


def get_user_token():
    params_path = os.path.join(BASE_DIR, "dawn/client.ini")
    app_params = QSettings(params_path, QSettings.IniFormat)
    jwt_token = app_params.value("USER/BEARER")
    if jwt_token:
        token = "Bearer " + jwt_token
    else:
        token = "Bearer "
    return token

