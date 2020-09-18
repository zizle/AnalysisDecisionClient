# _*_ coding:utf-8 _*_
# @File  : frameless.py
# @Time  : 2020-08-28 10:28
# @Author: zizle

""" 主窗口事件处理 """
import os
import json
from PyQt5.QtWidgets import qApp, QLabel
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, QSettings, QTimer
from frames.passport import UserPassport
from frames.user_center import UserCenter
from settings import SERVER_API, ADMINISTRATOR, BASE_DIR, ONLINE_COUNT_INTERVAL, PLATE_FORM, SYS_BIT
from .frameless_ui import FrameLessWindowUI

from admin.operator.user_manager import UserManager
from admin.operator.client_manager import ClientManage
from admin.operator.variety import VarietyAdmin
from admin.product.short_message import ShortMessageAdmin
from admin.user_data import UserDataMaintain
from admin.exchange_spider import ExchangeSpider
from admin.operator.user_extension import UserExtensionPage
from frames.homepage import Homepage
from frames.product import ProductPage
from frames.industry.variety_data import VarietyData
from frames.exchange_query import ExchangeQuery
from frames.net_position import NetPosition
from frames.about_us import CheckVersion
from popup.update import NewVersionPopup


class ClientMainApp(FrameLessWindowUI):
    """ 主程序 """
    def __init__(self, *args, **kwargs):
        super(ClientMainApp, self).__init__(*args, **kwargs)

        qApp.applicationStateChanged.connect(self.application_state_changed)

        self.user_online_timer = QTimer(self)                                              # 用户登录时间定时器
        self.user_online_timer.timeout.connect(self.update_user_online_time)

        self.navigation_bar.username_button.clicked.connect(self.clicked_username_button)  # 点击登录或跳转个人中心
        self.navigation_bar.logout_button.clicked.connect(self.user_logout_proxy)          # 用户退出
        self.navigation_bar.menu_clicked.connect(self.enter_module_page)

        self.set_default_homepage()

        self._user_login_automatic()                                                      # 用户启动自动登录

        if not self.user_online_timer.isActive():                       # 开启在线时间统计
            self.user_online_timer.start(ONLINE_COUNT_INTERVAL)

        self._checking_new_version()

    def _checking_new_version(self):
        """ 检测新版本 """
        # 获取当前版本号
        json_file = os.path.join(BASE_DIR, "classini/update_{}_{}.json".format(PLATE_FORM, SYS_BIT))
        if not os.path.exists(json_file):
            return
        with open(json_file, "r", encoding="utf-8") as jf:
            update_json = json.load(jf)
        is_manager = 1 if ADMINISTRATOR else 0
        url = SERVER_API + "check_version/?version={}&plateform={}&sys_bit={}&is_manager={}".format(
            update_json["VERSION"], PLATE_FORM, SYS_BIT, is_manager)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(request)
        reply.finished.connect(self.last_version_back)

    def last_version_back(self):
        """ 检测版本结果 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            return
        data = reply.readAll().data()
        u_data = json.loads(data.decode("utf-8"))
        if u_data["update_needed"]:
            p = NewVersionPopup(self)
            p.to_update.connect(self.to_update_page)
            p.show()
        else:
            pass
        reply.deleteLater()

    def to_update_page(self):
        """ 前往版本更新页面 """
        self.set_system_page("0_0_1")

    def application_state_changed(self, state):
        """ 应用程序状态发生变化 """
        if state == Qt.ApplicationInactive:
            if self.user_online_timer.isActive():
                self.user_online_timer.stop()
        elif state == Qt.ApplicationActive:
            if not self.user_online_timer.isActive():
                self.user_online_timer.start(ONLINE_COUNT_INTERVAL)

    def update_user_online_time(self):
        """ 更新用户 (客户端)在线时间"""
        client_ini_path = os.path.join(BASE_DIR, "dawn/client.ini")
        token_config = QSettings(client_ini_path, QSettings.IniFormat)
        is_logged = self.navigation_bar.get_user_login_status()
        client_uuid = token_config.value("TOKEN/UUID") if token_config.value("TOKEN/UUID") else ""
        user_token = ""
        if is_logged:
            user_token = token_config.value("USER/BEARER") if token_config.value("USER/BEARER") else ""
        token = "Bearer " + user_token
        network_manager = getattr(qApp, '_network')
        url = SERVER_API + "user/online/?machine_uuid=" + client_uuid
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), token.encode("utf-8"))
        reply = network_manager.put(request, None)  # 此处不用post：发现Qt查询参数丢失
        reply.finished.connect(reply.deleteLater)

    def set_default_homepage(self):
        """ 设置默认的首页 """
        homepage = Homepage()
        self.center_widget.setCentralWidget(homepage)

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

    def user_logout_proxy(self):
        """ 用户主动点击退出
            由于QPushButton的clicked信号默认传过来的参数为False。此函数为代理
        """
        self.user_logout()

    def user_logout(self, to_homepage=True):
        """ 用户退出
        """
        print(to_homepage)
        self.navigation_bar.username_button.setText('登录')
        self.navigation_bar.set_user_login_status(status=0)
        self.navigation_bar.logout_button.hide()
        # 跳转到首页
        if to_homepage:
            self.set_default_homepage()

    def set_system_page(self, module_id):
        """ 进入关于系统 """
        print(module_id)
        if module_id == "0_0_1":
            page = CheckVersion()  # 版本检查页面
        else:
            page = QLabel(
                "暂未开放···\n更多资讯请访问【首页】查看.",
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter)
        self.center_widget.setCentralWidget(page)

    def enter_module_page(self, module_id, module_text):
        """ 根据菜单,进入不同的功能界面 """
        if module_id == "0":
            self.set_default_homepage()
            return
        if module_id[:3] == "0_0":
            self.set_system_page(module_id)  # 进入关于系统的菜单
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
            if reply.error() == 201 and self.navigation_bar.get_user_login_status():
                self.user_logout(to_homepage=False)  # 不跳转首页

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
        if module_id == "1":             # 产品服务
            page = ProductPage()
        elif module_id == "2_0":         # 产业数据库
            page = VarietyData()
        elif module_id == "2_1":         # 交易所数据
            page = ExchangeQuery()
        elif module_id == "2_2":         # 品种净持仓
            page = NetPosition()
        elif module_id == "-9_1_0":
            page = VarietyAdmin()        # 后台管理-品种管理
        elif module_id == "-9_1_1":      # 后台管理-用户管理
            page = UserManager()
        elif module_id == "-9_1_2":
            page = ClientManage()
        elif module_id == "-9_1_3":      # 后台管理-研究员微信ID
            page = UserExtensionPage()
        elif module_id == "-9_2_0":
            page = ShortMessageAdmin()   # 短信通管理
        elif module_id == "-9_3_0":      # 后台管理-产业数据库
            page = UserDataMaintain()
        elif module_id == "-9_3_1":
            page = ExchangeSpider()
        else:
            page = QLabel(
                "「" + module_text + "」暂未开放···\n更多资讯请访问【首页】查看.",
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter)
        return page

