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
from settings import SERVER_ADDR, SERVER_API, logger, ADMINISTRATOR, BASE_DIR
from utils.client import get_client_uuid
from .frameless_ui import FrameLessWindowUI


class ClientMainApp(FrameLessWindowUI):
    def __init__(self, *args, **kwargs):
        super(ClientMainApp, self).__init__(*args, **kwargs)
        self.client_uuid = None

        qApp.applicationStateChanged.connect(self.application_state_changed)

        self.client_open_timer = QTimer(self)                                              # 客户端开启时间定时器
        self.client_open_timer.timeout.connect(self.update_client_open_time)               # 更新客户端开启时间

        self.user_online_timer = QTimer(self)                                              # 用户登录时间定时器
        self.user_online_timer.timeout.connect(self.update_user_online_time)

        self.navigation_bar.username_button.clicked.connect(self.clicked_username_button)  # 点击登录或跳转个人中心
        self.navigation_bar.logout_button.clicked.connect(self.user_logout)                # 用户退出
        self.navigation_bar.menu_clicked.connect(self.enter_module_page)

        self._bind_global_network_manager()                                               # 绑定全局网络管理器

        self._add_client_to_server()                                                      # 记录客户端

        self.set_default_homepage()

    def action_online_timer(self):
        """ 开启在线的统计计时器 """
        client_ini_path = os.path.join(BASE_DIR, "dawn/client.ini")
        client_config = QSettings(client_ini_path, QSettings.IniFormat)
        is_logged = client_config.value('USER/LOGGED')
        if is_logged:  # 用户已登录了
            if not self.user_online_timer.isActive():
                self.user_online_timer.start(120000)
            if self.client_open_timer.isActive():
                self.client_open_timer.stop()
        else:  # 用户未登录
            if not self.client_open_timer.isActive():
                self.client_open_timer.start(120000)
            if self.user_online_timer.isActive():
                self.user_online_timer.stop()

    def inaction_online_timer(self):
        """ 关闭统计计时器 """
        if self.client_open_timer.isActive():
            self.client_open_timer.stop()
        if self.user_online_timer.isActive():
            self.user_online_timer.stop()

    def application_state_changed(self, state):
        """ 应用程序状态发生变化 """
        if state == Qt.ApplicationInactive:
            print("应用程序不活跃了")
            self.inaction_online_timer()
        elif state == Qt.ApplicationActive:
            print("应用程序活跃了")
            self.action_online_timer()
        print("用户定时器状态:", self.user_online_timer.isActive())
        print("客户端定时器状态:", self.client_open_timer.isActive())

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
        self.action_online_timer()                                      # 开启在线定时器

        print("用户定时器状态:", self.user_online_timer.isActive())
        print("客户端定时器状态:", self.client_open_timer.isActive())

    def update_client_open_time(self):
        """ 更新客户端开启时间 """
        network_manager = getattr(qApp, '_network')
        url = SERVER_API + "client/online/?machine_uuid=" + self.client_uuid
        reply = network_manager.put(QNetworkRequest(QUrl(url)), None)   # 此处不用post：发现Qt查询参数丢失
        reply.finished.connect(reply.deleteLater)

    def update_user_online_time(self):
        """ 更新用户在线时间 (停止客户端计时)"""

    def set_default_homepage(self):
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
            try:
                center_widget = UserPassport()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
        self.center_widget.setCentralWidget(center_widget)

    def user_login_successfully(self, username):
        """ 用户登录成功 """
        self.navigation_bar.username_button.setText(username)
        self.navigation_bar.set_user_login_status(status=1)
        self.navigation_bar.logout_button.show()
        # 跳转到首页
        self.set_default_homepage()

    def user_logout(self):
        """ 用户退出 """
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

        client_params = QSettings('dawn/initial.ini', QSettings.IniFormat)

        network_manager = getattr(qApp, '_network')
        url = SERVER_ADDR + 'module_access/'
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")
        body_data = {
            "module_id": module_id,
            "module_text": module_text,
            "utoken": client_params.value("AUTHORIZATION"),
            "client": client_params.value("machine")
        }
        reply = network_manager.post(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.access_module_reply)

    def access_module_reply(self):
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            center_widget = QLabel(
                "网络开小差了,检查网络设置!\n{}".format(reply.error()),
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter
            )
        else:
            data = json.loads(data.decode('utf-8'))
            if data["allow_in"]:
                # 进入相应模块
                center_widget = self.get_module_page(data["module_id"], data["module_text"])
            else:
                center_widget = QLabel(
                    data["message"],
                    styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                    alignment=Qt.AlignCenter
                )
        reply.deleteLater()
        self.center_widget.setCentralWidget(center_widget)

    @staticmethod
    def get_module_page(module_id, module_text):
        """ 通过权限验证,进入功能页面 """
        print(module_id, module_text, "允许进入")
        page = QLabel(
            "「" + module_text + "」暂未开放···\n更多资讯请访问【首页】查看.",
            styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
            alignment=Qt.AlignCenter)
        return page

