# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import re
import json
import base64
import requests
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal

import settings


# 登录弹窗
class LoginPopup(QDialog):
    user_listed = pyqtSignal(dict)  # 登录成功发出信号

    def __init__(self, *args, **kwargs):
        super(LoginPopup, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(spacing=0)
        # 手机
        phone_layout = QHBoxLayout()
        phone_label = QLabel()
        phone_label.setPixmap(QPixmap('media/passport_icon/phone.png'))
        phone_layout.addWidget(phone_label)
        # 填写手机
        self.phone_edit = QLineEdit(textEdited=self.phone_editing)
        phone_layout.addWidget(self.phone_edit)
        layout.addLayout(phone_layout)
        # 手机号错误提示框
        self.phone_error = QLabel()
        layout.addWidget(QLabel(parent=self, objectName='phoneError'))
        # 密码
        psd_layout = QHBoxLayout()
        password_label = QLabel()
        password_label.setPixmap(QPixmap('media/passport_icon/password.png'))
        psd_layout.addWidget(password_label)
        # 填写密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        psd_layout.addWidget(self.password_edit)
        layout.addLayout(psd_layout)
        # 密码错误提示框
        layout.addWidget(QLabel(parent=self, objectName='psdError'))
        # 记住密码
        remember_layout = QHBoxLayout(spacing=2)
        # 点击事件由代码不触发
        self.remember_psd = QCheckBox('记住密码', objectName='rememberCheck', clicked=self.clicked_remember_psd)
        remember_layout.addWidget(self.remember_psd)
        # 记住登录
        self.remember_login = QCheckBox('自动登录', objectName='rememberCheck', clicked=self.clicked_auto_login)
        remember_layout.addWidget(self.remember_login)
        remember_layout.addStretch()
        layout.addLayout(remember_layout)
        # 登录错误框
        layout.addWidget(QLabel(parent=self, objectName='loginError'))
        # 确认登录
        login_button = QPushButton('登录', clicked=self.commit_login, objectName='loginBtn')
        layout.addWidget(login_button)
        # 样式
        self.setWindowTitle('登录')
        self.setMinimumWidth(300)
        self.setStyleSheet("""
        #phoneError, #psdError, #loginError{
            color: rgb(200,50,30)
        }
        #rememberCheck{
            color: rgb(100,100,100)
        }
        #loginBtn{
            background-color:rgb(46,158,224);
            color: rgb(240,240,240);
            font-weight:bold;
            min-height:28px;
            border:none;
        }
        #loginBtn:pressed{
            background-color:rgb(28,76,202);
        }
        """)
        phone_label.setFixedSize(36, 35)
        phone_label.setScaledContents(True)
        self.phone_edit.setFixedHeight(35)
        password_label.setScaledContents(True)
        password_label.setFixedSize(36, 35)
        self.password_edit.setFixedHeight(35)
        # 布局
        self.setLayout(layout)
        self._init_account()

    # 正在输入账号
    def phone_editing(self):
        self.password_edit.setText('')
        self.remember_psd.setChecked(False)
        self.remember_login.setChecked(False)

    # 选择记住密码
    def clicked_remember_psd(self):
        remember = self.remember_psd.isChecked()
        phone, password = self.get_account()
        if not remember:
            # 保存用户名和密码
            password = ''
        account = json.dumps({'phone': phone, 'password': password})
        account = base64.b64encode(account.encode('utf-8')).decode('utf-8')
        settings.app_dawn.setValue('user', account)  # 保存用户名和密码

    # 选择自动登录
    def clicked_auto_login(self):
        auto_login = self.remember_login.isChecked()
        remember_psd_flag = self.remember_psd.isChecked()
        self.remember_psd.setChecked(False)  # 保存用户名和密码
        if auto_login:
            self.remember_psd.click()  # 保存用户资料
            settings.app_dawn.setValue('auto', 1)
        else:
            self.remember_psd.setChecked(remember_psd_flag)
            # 取消自动登录
            settings.app_dawn.setValue('auto', 0)
            # 删除token
            settings.app_dawn.remove('AUTHORIZATION')

    # 读取用户名填入
    def _init_account(self):
        user = settings.app_dawn.value('user')
        if user:
            account = base64.b64decode(user.encode('utf-8'))
            account = json.loads(account.decode('utf-8'))
            phone = account.get('phone', '')
            password = account.get('password', '')
            self.phone_edit.setText(phone)
            self.password_edit.setText(password)
            if password:
                self.remember_psd.setChecked(True)
            if settings.app_dawn.value('auto') == '1':
                self.remember_login.setChecked(True)

    # 获取手机号和密码
    def get_account(self):
        # 获取手机
        phone = re.match(r'^[1][3-9][0-9]{9}$', self.phone_edit.text())
        if not phone:
            phone = ''
        else:
            phone = phone.group()
        # 获取密码
        password = re.sub(r'\s+', '', self.password_edit.text())
        if not password:
            password = ''
        return phone, password

    # 获取手机号和密码提交登录
    def commit_login(self):
        phone, password = self.get_account()
        if not phone:
            self.findChild(QLabel, 'phoneError').setText('请输入正确的手机号')
            return
        if not password:
            self.findChild(QLabel, 'psdError').setText('请输入密码')
            return
        # 判断记住密码和自动登录的情况

        # 登录成功
        if self._login_post(phone, password):
            self.close()

    # 提交登录
    def _login_post(self, phone, password):
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'login/',
                headers={
                    "Content-Type": "application/json;charset=utf8",
                    "AUTHORIZATION": settings.app_dawn.value('AUTHORIZATION'),
                },
                data=json.dumps({
                    "phone": phone,
                    "password": password,
                    "machine_code":settings.app_dawn.value('machine', '')
                }),
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.findChild(QLabel, 'loginError').setText(str(e))
            # 移除token
            settings.app_dawn.remove('AUTHORIZATION')
            return False
        else:
            self.user_listed.emit(response['user_data'])
            return True