# _*_ coding:utf-8 _*_
# @File  : configs.py
# @Time  : 2020-08-20 13:41
# @Author: zizle
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER = "http://210.13.218.130:9001/api/"
LOCAL_SPIDER_SRC = os.path.join(BASE_DIR, "sources/")  # 爬取保存文件的本地文件夹

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
]