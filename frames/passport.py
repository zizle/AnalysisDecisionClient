# _*_ coding:utf-8 _*_
# @File  : passport.py
# @Time  : 2020-08-28 16:09
# @Author: zizle
from PyQt5.QtCore import pyqtSignal
from .passport_ui import PassportUI


class UserPassport(PassportUI):
    """ 登录注册界面 """
    username_signal = pyqtSignal(str)  # 登录成功,发出用户名信号

    def __init__(self, *args, **kwargs):
        super(UserPassport, self).__init__(*args, **kwargs)
        self.login_button.clicked.connect(self.user_to_login)

    def user_to_login(self):
        """ 用户登录 """
        self.username_signal.emit("用户名1")