# _*_ coding:utf-8 _*_
# Author: zizle  QQ:462894999
import os
import time
import logging
from PyQt5.QtCore import QSettings
WINDOW_TITLE = '瑞达期货研究院分析决策系统管理端'  # 1.3.1
# SERVER_ADDR = "http://210.13.218.130:9002/"
SERVER_ADDR = "http://127.0.0.1:5000/"

SERVER_API = "http://127.0.0.1:8000/api/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMINISTRATOR = True

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

SYSTEM_MENUS = [
    {"id": "0", "name": "首页", "logo": "", "children": None},
    {"id": "2", "name": "产品服务", "logo": "", "children": None},
    {"id": "111", "name": "测试", "logo": "", "children": [
        {"id": "111_1", "name": "测试——1", "logo": "", "children": None},
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
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s[line:%(lineno)d]"
    )
    handler.setFormatter(logger_format)
    return handler


logger = logging.getLogger('errorlog')
logger.addHandler(config_logger_handler())
