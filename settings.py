# _*_ coding:utf-8 _*_
# Author: zizle  QQ:462894999
import os
import time
import logging
from PyQt5.QtCore import QSettings
WINDOW_TITLE = '期货分析助手管理端'  # 1.3.1
# SERVER_ADDR = "http://210.13.218.130:9002/"
SERVER_ADDR = "http://127.0.0.1:5000/"

SERVER_API = "http://127.0.0.1:8000/api/"
SERVER_HOST = "http://127.0.0.1:8000/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMINISTRATOR = True

ONLINE_COUNT_INTERVAL = 120000  # 毫秒

USER_AGENT = 'RuiDa_ADSClient_VERSION_1.0.1'
# app设置
app_dawn = QSettings('dawn/initial.ini', QSettings.IniFormat)
cache_dawn = QSettings('dawn/cache.ini', QSettings.IniFormat)
# 与后端对应的静态文件路径
STATIC_PREFIX = SERVER_ADDR + 'ads/'
# 首页广告变化速率，单位毫秒
IMAGE_SLIDER_RATE = 3000
# 标题栏高度
TITLE_BAR_HEIGHT = 27
# 菜单栏高度
NAVIGATION_BAR_HEIGHT = 20

# 支持多级(但模块权限仅遍历3级)
SYSTEM_MENUS = [
    {"id": "0", "name": "首页", "logo": "", "children": None},
    {"id": "1", "name": "产品服务", "logo": "", "children": None},
    {"id": "2", "name": "行业数据", "logo": "", "children": [
        {"id": "2_0", "name": "产业数据库", "logo": "", "children": None},
        {"id": "2_1", "name": "交易所数据", "logo": "", "children": None},
        {"id": "2_2", "name": "品种净持仓", "logo": "", "children": None},
    ]},
    {"id": "-9", "name": "后台管理", "logo": "", "children": [
        {"id": "-9_1", "name": "运营管理", "logo": "", "children": [
            {"id": "-9_1_0", "name": "品种管理", "logo": "", "children": None},
            {"id": "-9_1_1", "name": "用户管理", "logo": "", "children": None},
            {"id": "-9_1_2", "name": "客户端管理", "logo": "", "children": None},
        ]},
        {"id": "-9_0", "name": "首页管理", "logo": "", "children": [
            {"id": "-9_0_0", "name": "公告信息", "logo": "", "children": None},
            {"id": "-9_0_1", "name": "广告展示", "logo": "", "children": None},
            {"id": "-9_0_2", "name": "常规报告", "logo": "", "children": None},
            {"id": "-9_0_3", "name": "交易通知", "logo": "", "children": None},
            {"id": "-9_0_4", "name": "现货数据", "logo": "", "children": None},
            {"id": "-9_0_5", "name": "财经日历", "logo": "", "children": None},
        ]},
        {"id": "-9_2", "name": "产品服务", "logo": "", "children": None},
        {"id": "-9_3", "name": "行业数据", "logo": "", "children": [
            {"id": "-9_3_0", "name": "产业数据库", "logo": "", "children": None},
            {"id": "-9_3_1", "name": "交易所数据", "logo": "", "children": None},
        ]},
    ]},
]


# 设置日志记录
def make_dir(dir_path):
    path = dir_path.strip()
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def config_logger_handler():
    # 日志配置
    log_folder = os.path.join(BASE_DIR, "logs/")
    make_dir(log_folder)
    log_file_name = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_path = log_folder + os.sep + log_file_name

    handler = logging.FileHandler(log_file_path, encoding='UTF-8')
    handler.setLevel(logging.ERROR)
    # "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s[line:%(lineno)d]"
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s : %(message)s"
    )
    handler.setFormatter(logger_format)
    return handler


logger = logging.getLogger('errorlog')
logger.addHandler(config_logger_handler())
