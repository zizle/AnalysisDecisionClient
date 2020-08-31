# _*_ coding:utf-8 _*_
# @File  : passport.py
# @Time  : 2020-08-28 16:09
# @Author: zizle
import os
import re
import uuid
import json
import base64
from PyQt5.QtWidgets import qApp
from PyQt5.QtCore import pyqtSignal, QUrl, QSettings, QTimer
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtGui import QPixmap
from settings import SERVER_API, BASE_DIR
from utils.multipart import generate_multipart_data
from .passport_ui import PassportUI


class UserPassport(PassportUI):
    """ 登录注册界面 """
    username_signal = pyqtSignal(str)  # 登录成功,发出用户名信号

    def __init__(self, *args, **kwargs):
        super(UserPassport, self).__init__(*args, **kwargs)
        self._code_uuid = ""
        self.text_animation_timer = QTimer(self)
        self.text_animation_timer.timeout.connect(self.network_tip_animation)

        self.login_widget.to_register_button.clicked.connect(self.to_register_page)             # 切换到注册页面
        self.register_widget.to_login_button.clicked.connect(self.to_login_page)                # 切换到登录页面
        self.register_widget.image_code_show.refresh_image_code.connect(self.get_image_code)    # 图片验证码点击更换

        self.register_widget.check_phone_unique.connect(self.checking_phone_unique)             # 请求手机号是否唯一

        self.login_widget.login_button.clicked.connect(self.user_commit_login)                  # 用户点击登录
        self.register_widget.register_button.clicked.connect(self.user_commit_register)         # 用户点击注册

        self.get_image_code()  # 初始获取验证码

    def network_tip_animation(self):
        """ 网络请求中动态提示 """
        if self.currentIndex() == 1:
            tips = self.register_widget.register_button.text()
            tip_points = tips.split(' ')[1]
            if len(tip_points) > 2:
                self.register_widget.register_button.setText("正在注册 ")
            else:
                self.register_widget.register_button.setText("正在注册 " + "·" * (len(tip_points) + 1))
        else:
            tips = self.login_widget.login_button.text()
            tip_points = tips.split(' ')[1]
            if len(tip_points) > 2:
                self.login_widget.login_button.setText("正在登录 ")
            else:
                self.login_widget.login_button.setText("正在登录 " + "·" * (len(tip_points) + 1))

    def user_to_login(self):
        """ 用户登录 """
        self.username_signal.emit("用户名1")

    def to_register_page(self):
        """ 切换到注册页面 """
        self.setCurrentIndex(1)
        self.text_animation_timer.stop()

    def to_login_page(self):
        """ 切换到登录页面 """
        self.setCurrentIndex(0)
        self.text_animation_timer.stop()

    def get_image_code(self):
        """ 获取图片验证码 """
        self._code_uuid = ''.join(str(uuid.uuid4()).split("-"))  # 保存code_uuid方便使用
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'image_code/?code_uuid=' + self._code_uuid
        request = QNetworkRequest(QUrl(url))
        reply = network_manager.get(request)
        reply.finished.connect(self.image_code_back)

    def image_code_back(self):
        """ 获取到image_code """
        reply = self.sender()
        data = reply.readAll().data()
        reply.deleteLater()
        del reply
        pix_map = QPixmap()
        pix_map.loadFromData(data)
        self.register_widget.image_code_show.setPixmap(pix_map)  # 注册验证码

    def checking_phone_unique(self, phone):
        """ 请求手机号是否唯一 """
        if not re.match(r'^[1][3-9][0-9]{9}$', phone):
            self.register_widget.phone_error.setText("手机号格式有误!")
            return
        # 发送请求
        url = SERVER_API + "user/phone-exists/?phone=" + phone
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.phone_unique_back)

    def phone_unique_back(self):
        """ 请求手机是否唯一返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        if data["is_exists"]:
            self.register_widget.phone_error.setText("手机号已存在!")
        reply.deleteLater()

    def user_commit_register(self):
        """ 用户注册 """
        phone = self.register_widget.phone_edit.text().strip()
        if not re.match(r'^[1][3-9][0-9]{9}$', phone):
            self.register_widget.phone_error.setText("手机号格式有误!")
            return
        email = self.register_widget.email_edit.text().strip()
        if not re.match(r'^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$', email):
            self.register_widget.email_error.setText("请填写正确的邮箱!")
            return
        password_0 = self.register_widget.password_edit_0.text().strip()
        password_1 = self.register_widget.password_edit_1.text().strip()
        if not re.match(r'^[a-zA-Z_0-9!#.]{6,20}$', password_0):
            self.register_widget.password_error_0.setText("密码仅允许大小写字母数字的6-20个字符组成")
            return
        if password_0 != password_1:
            self.register_widget.password_error_1.setText("两次输入密码不一致!")
            return
        config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        client_configs = QSettings(config_path, QSettings.IniFormat)

        # 获取注册信息
        register_dict = {
            "username": self.register_widget.username_edit.text().strip(),
            "phone": base64.b64encode(phone.encode('utf-8')).decode('utf-8'),
            "email": self.register_widget.email_edit.text().strip(),
            "password": base64.b64encode(password_1.encode('utf-8')).decode('utf-8'),
            "client_token": client_configs.value('TOKEN/UUID'),
            "input_code": self.register_widget.image_code_edit.text().strip(),
            "code_uuid": self._code_uuid
        }
        self.register_widget.register_button.disconnect()   # 屏蔽再次点击信号

        if not self.text_animation_timer.isActive():
            self.text_animation_timer.start(400)

        multi_data = generate_multipart_data(register_dict)

        network_manager = getattr(qApp, "_network")

        url = SERVER_API + "register/"
        request = QNetworkRequest(QUrl(url))

        reply = network_manager.post(request, multi_data)
        reply.finished.connect(self.user_register_back)
        multi_data.setParent(reply)

    def user_register_back(self):
        """ 用户注册请求返回 """
        self.text_animation_timer.stop()
        self.register_widget.register_button.setText("立即注册 ")
        self.register_widget.register_button.clicked.connect(self.user_commit_register)  # 恢复点击信号
        reply = self.sender()
        if reply.error():
            self.register_widget.register_error.setText("注册失败:{}".format(reply.error()))
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        self.register_widget.register_error.setText(data["message"])
        reply.deleteLater()

    def user_commit_login(self):
        """ 用户登录 """

