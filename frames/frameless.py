# _*_ coding:utf-8 _*_
# @File  : frameless.py
# @Time  : 2020-08-28 10:28
# @Author: zizle

""" 主窗口事件处理 """

import json
from PyQt5.QtWidgets import qApp, QLabel
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, QSettings
from frames.passport import UserPassport
from frames.user_center import UserCenter
from settings import SERVER_ADDR
from .frameless_ui import FrameLessWindowUI


class ClientMainApp(FrameLessWindowUI):
    def __init__(self, *args, **kwargs):
        super(ClientMainApp, self).__init__(*args, **kwargs)
        self.set_default_homepage()

        self.navigation_bar.username_button.clicked.connect(self.clicked_username_button)  # 点击登录或跳转个人中心
        self.navigation_bar.logout_button.clicked.connect(self.user_logout)                # 用户退出
        self.navigation_bar.menu_clicked.connect(self.enter_module_page)

        self.bind_global_network_manager()

    def bind_global_network_manager(self):
        """ 绑定全局网络管理器 """
        if not hasattr(qApp, "_network"):
            network_manager = QNetworkAccessManager(self)
            setattr(qApp, "_network", network_manager)

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

