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
from PyQt5.QtCore import pyqtSignal, QUrl, QSettings, QTimer, Qt
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
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
        self.login_widget.image_code_show.refresh_image_code.connect(self.get_image_code)       # 登录界面点击图片验证码

        self.register_widget.check_phone_unique.connect(self.checking_phone_unique)             # 请求手机号是否唯一

        self.login_widget.login_button.clicked.connect(self.user_commit_login)                  # 用户点击登录
        self.register_widget.register_button.clicked.connect(self.user_commit_register)         # 用户点击注册

        self.get_image_code()  # 初始获取验证码

        self.initialize_account()  # 初始填写用户名和密码

    def initialize_account(self):
        """ 初始化填充用户名和密码 """
        client_config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        app_configs = QSettings(client_config_path, QSettings.IniFormat)
        phone = app_configs.value("USER/USER")
        password = app_configs.value("USER/USERP")
        if phone:
            phone = base64.b64decode(phone.encode('utf-8')).decode('utf-8')  # 解码
            self.login_widget.phone_edit.setText(phone)
            if password:
                password = base64.b64decode(password.encode('utf-8')).decode('utf-8')  # 解码
                self.login_widget.password_edit.setText(password)
                self.login_widget.remember_psd.setChecked(True)

    def remember_checked_handler(self):
        """ 记住密码状态改变 """
        client_config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        app_configs = QSettings(client_config_path, QSettings.IniFormat)
        state = self.login_widget.remember_psd.checkState()
        if state == Qt.Checked:
            phone = self.login_widget.phone_edit.text().strip()
            password = self.login_widget.password_edit.text().strip()
            encrypt_phone = base64.b64encode(phone.encode('utf-8')).decode('utf-8')
            encrypt_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            app_configs.setValue("USER/USER", encrypt_phone)
            app_configs.setValue("USER/USERP", encrypt_password)
        else:
            app_configs.remove("USER/USER")
            app_configs.remove("USER/USERP")
            app_configs.remove("USER/AUTOLOGIN")

    def remember_login_handler(self):
        """ 自动登录状态改变 """
        client_config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        app_configs = QSettings(client_config_path, QSettings.IniFormat)
        state = self.login_widget.remember_login.checkState()
        if state == Qt.Checked:
            if not self.login_widget.remember_psd.isChecked():
                self.login_widget.remember_psd.setChecked(True)
            self.remember_checked_handler()   # 记住登录,手动调用记住密码
            app_configs.setValue("USER/AUTOLOGIN", 1)
        else:
            # 移除自动登录标记
            app_configs.remove("USER/AUTOLOGIN")

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
        self.login_widget.image_code_show.setPixmap(pix_map)  # 登录验证码
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
            "code_uuid": self._code_uuid,
            "client_uuid": client_configs.value("TOKEN/UUID")
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
        self.remember_checked_handler()  # 处理是否记住密码
        self.remember_login_handler()    # 处理是否自动登录

        config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        client_configs = QSettings(config_path, QSettings.IniFormat)

        phone = self.login_widget.phone_edit.text().strip()
        password = self.login_widget.password_edit.text().strip()
        user_dict = {
            "phone": base64.b64encode(phone.encode('utf-8')).decode('utf-8'),        # 加密
            "password": base64.b64encode(password.encode('utf-8')).decode('utf-8'),
            "input_code": self.login_widget.image_code_edit.text().strip(),
            "code_uuid": self._code_uuid,
            "client_uuid": client_configs.value("TOKEN/UUID")
        }
        self.login_widget.login_button.disconnect()    # 断开信号
        if not self.text_animation_timer.isActive():
            self.text_animation_timer.start(400)

        multi_data = generate_multipart_data(user_dict)

        network_manager = getattr(qApp, "_network")

        url = SERVER_API + "login/"
        request = QNetworkRequest(QUrl(url))

        reply = network_manager.post(request, multi_data)
        reply.finished.connect(self.user_login_back)
        multi_data.setParent(reply)

    def user_login_back(self):
        """ 用户登录结果返回 """
        self.text_animation_timer.stop()
        self.login_widget.login_button.setText("登录 ")
        self.login_widget.login_button.clicked.connect(self.user_commit_login)  # 恢复点击信号
        reply = self.sender()
        if reply.error():
            if reply.error() == QNetworkReply.ProtocolInvalidOperationError:
                message = "验证码错误!"
            elif reply.error() == QNetworkReply.AuthenticationRequiredError:
                message = "用户名或密码错误!"
            elif reply.error() == QNetworkReply.ContentAccessDenied:
                message = "您不能在此客户端登录!"
            else:
                message = "登录失败:{}".format(reply.error())
            self.login_widget.login_error.setText(message)
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()
        # 写入token
        client_config_path = os.path.join(BASE_DIR, "dawn/client.ini")
        app_configs = QSettings(client_config_path, QSettings.IniFormat)
        app_configs.setValue("USER/BEARER", data["access_token"])
        app_configs.setValue("USER/TTYPE", "bearer")
        # 发出登录成功的信号
        self.username_signal.emit(data["show_username"])
