# _*_ coding:utf-8 _*_
# @File  : frameless.py
# @Time  : 2020-08-28 10:28
# @Author: zizle

""" 主窗口事件处理 """
import os
import sys
import json
from PyQt5.QtWidgets import qApp, QLabel
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, QSettings, QTimer
from frames.passport import UserPassport
from frames.user_center import UserCenter
from settings import SERVER_ADDR, SERVER_API, logger, ADMINISTRATOR, BASE_DIR, ONLINE_COUNT_INTERVAL
from utils.client import get_client_uuid
from .frameless_ui import FrameLessWindowUI

from admin.user_manager import UserManager


class ClientMainApp(FrameLessWindowUI):
    """ 主程序 """
    def __init__(self, *args, **kwargs):
        super(ClientMainApp, self).__init__(*args, **kwargs)
        self.client_uuid = None

        qApp.applicationStateChanged.connect(self.application_state_changed)

        self.user_online_timer = QTimer(self)                                              # 用户登录时间定时器
        self.user_online_timer.timeout.connect(self.update_user_online_time)

        self.navigation_bar.username_button.clicked.connect(self.clicked_username_button)  # 点击登录或跳转个人中心
        self.navigation_bar.logout_button.clicked.connect(self.user_logout)                # 用户退出
        self.navigation_bar.menu_clicked.connect(self.enter_module_page)

        self._bind_global_network_manager()                                               # 绑定全局网络管理器

        self._add_client_to_server()                                                      # 记录客户端

        self.set_default_homepage()

        self._user_login_automatic()                                                      # 用户启动自动登录

    def application_state_changed(self, state):
        """ 应用程序状态发生变化 """
        if state == Qt.ApplicationInactive:
            if self.user_online_timer.isActive():
                self.user_online_timer.stop()
        elif state == Qt.ApplicationActive:
            if not self.user_online_timer.isActive():
                self.user_online_timer.start(ONLINE_COUNT_INTERVAL)

    def _bind_global_network_manager(self):
        """ 绑定全局网络管理器 """
        if not hasattr(qApp, "_network"):
            network_manager = QNetworkAccessManager(self)
            setattr(qApp, "_network", network_manager)

    def _add_client_to_server(self):
        """ 新增客户端 """
        client_uuid = get_client_uuid()
        if not client_uuid:
            self.close()
            sys.exit(-1)

        client_info = {
            'client_name': '',
            'machine_uuid': client_uuid,
            'is_manager': ADMINISTRATOR
        }
        network_manager = getattr(qApp, '_network')
        url = SERVER_API + "client/"
        reply = network_manager.post(QNetworkRequest(QUrl(url)), json.dumps(client_info).encode('utf-8'))
        reply.finished.connect(self.add_client_reply)

    def add_client_reply(self):
        """ 添加客户端的信息返回了 """
        reply = self.sender()
        if reply.error():
            logger.error("New Client ERROR!{}".format(reply.error()))
            sys.exit(-1)
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()
        # 将信息写入token
        self.client_uuid = data["client_uuid"]
        client_ini_path = os.path.join(BASE_DIR, "dawn/client.ini")
        token_config = QSettings(client_ini_path, QSettings.IniFormat)
        token_config.setValue("TOKEN/UUID", self.client_uuid)
        if not self.user_online_timer.isActive():                       # 开启在线时间统计
            self.user_online_timer.start(ONLINE_COUNT_INTERVAL)

    def update_user_online_time(self):
        """ 更新用户 (客户端)在线时间"""
        client_ini_path = os.path.join(BASE_DIR, "dawn/client.ini")
        token_config = QSettings(client_ini_path, QSettings.IniFormat)
        is_logged = self.navigation_bar.get_user_login_status()
        user_token = ""
        if is_logged:
            user_token = token_config.value("USER/BEARER") if token_config.value("USER/BEARER") else ""
        token = "Bearer " + user_token
        network_manager = getattr(qApp, '_network')
        url = SERVER_API + "user/online/?machine_uuid=" + self.client_uuid
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), token.encode("utf-8"))
        reply = network_manager.put(request, None)  # 此处不用post：发现Qt查询参数丢失
        reply.finished.connect(reply.deleteLater)

    def set_default_homepage(self):
        """ 设置默认的首页 """
        c = QLabel("    默认主窗口")
        self.center_widget.setCentralWidget(c)

    def clicked_username_button(self):
        """ 点击了登录/用户名
            未登录就跳转到登录页面,已登录则跳转到个人中心
        """
        username_button = self.sender()
        is_user_logged = getattr(username_button, 'is_logged')
        if is_user_logged:
            center_widget = UserCenter()
        else:
            center_widget = UserPassport()
            center_widget.username_signal.connect(self.user_login_successfully)
        self.center_widget.setCentralWidget(center_widget)

    def user_login_successfully(self, username):
        """ 用户登录成功 """
        self.navigation_bar.username_button.setText(username)
        self.navigation_bar.set_user_login_status(status=1)
        self.navigation_bar.logout_button.show()
        # 跳转到首页
        self.set_default_homepage()

    def _user_login_automatic(self):
        """ 用户自动登录 """
        configs_path = os.path.join(BASE_DIR, "dawn/client.ini")
        app_config = QSettings(configs_path, QSettings.IniFormat)
        is_auto_login = app_config.value("USER/AUTOLOGIN")
        client_uuid = app_config.value("TOKEN/UUID") if app_config.value("TOKEN/UUID") else ''
        if is_auto_login:  # 使用TOKEN自动登录
            user_token = app_config.value("USER/BEARER") if app_config.value("USER/BEARER") else ''
            url = SERVER_API + "user/token-login/?client=" + client_uuid
            request = QNetworkRequest(QUrl(url))
            token = "Bearer " + user_token
            request.setRawHeader("Authorization".encode("utf-8"), token.encode("utf-8"))
            network_manager = getattr(qApp, '_network')
            reply = network_manager.get(request)
            reply.finished.connect(self._user_login_automatic_reply)

    def _user_login_automatic_reply(self):
        """ 自动登录返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            center_widget = QLabel(
                "登录信息已经失效了···\n请重新登录后再进行使用,访问【首页】查看更多资讯。",
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter
            )
            self.center_widget.setCentralWidget(center_widget)
        else:
            data = json.loads(data.decode("utf-8"))
            self.user_login_successfully(data["show_username"])
        reply.deleteLater()

    def user_logout(self):
        """ 用户退出
        """
        self.navigation_bar.username_button.setText('登录')
        self.navigation_bar.set_user_login_status(status=0)
        self.navigation_bar.logout_button.hide()
        # 跳转到首页
        self.set_default_homepage()

    def enter_module_page(self, module_id, module_text):
        """ 根据菜单,进入不同的功能界面 """
        if module_id == "0":
            self.set_default_homepage()
            return

        client_params = QSettings('dawn/client.ini', QSettings.IniFormat)

        network_manager = getattr(qApp, '_network')
        url = SERVER_API + 'user/module-authenticate/'
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")
        user_token = client_params.value("USER/BEARER") if self.navigation_bar.get_user_login_status() else ''
        body_data = {
            "module_id": module_id,
            "module_text": module_text,
            "client_uuid": client_params.value("TOKEN/UUID"),
            "user_token": user_token
        }
        reply = network_manager.post(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.access_module_reply)

    def access_module_reply(self):
        reply = self.sender()
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        reply.deleteLater()
        if reply.error():
            center_widget = QLabel(
                data.get("detail", reply.error()),
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter
            )
        else:
            if data["authenticate"]:
                # 进入相应模块
                center_widget = self.get_module_page(data["module_id"], data["module_text"])
            else:
                center_widget = QLabel(
                    data["message"],
                    styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                    alignment=Qt.AlignCenter
                )

        self.center_widget.setCentralWidget(center_widget)

    @staticmethod
    def get_module_page(module_id, module_text):
        """ 通过权限验证,进入功能页面 """
        print(module_id, module_text, "允许进入")
        if module_id == "-9_1_1":                                  # 后台管理-用户管理
            page = UserManager()
        else:
            page = QLabel(
                "「" + module_text + "」暂未开放···\n更多资讯请访问【首页】查看.",
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter)
        return page

