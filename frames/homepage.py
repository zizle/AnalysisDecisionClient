# _*_ coding:utf-8 _*_
# @File  : homepage.py
# @Time  : 2020-07-19 15:14
# @Author: zizle
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings, QUrl
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from .homepage_ui import HomepageUI
from configs import BASE_DIR, SERVER


class Homepage(HomepageUI):
    """ 首页业务 """
    def __init__(self, *args, **kwargs):
        super(Homepage, self).__init__(*args, **kwargs)

