# _*_ coding:utf-8 _*_
# @File  : passport_ui.py
# @Time  : 2020-08-28 16:07
# @Author: zizle

from PyQt5.QtWidgets import QWidget, QPushButton


class PassportUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(PassportUI, self).__init__(*args, **kwargs)
        self.login_button = QPushButton("登录", self)