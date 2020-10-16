# _*_ coding:utf-8 _*_
# @File  : user_center_ui.py
# @Time  : 2020-08-28 16:25
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QLabel


class UserCenterUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(UserCenterUI, self).__init__(*args, **kwargs)
        QLabel("个人中心", self)