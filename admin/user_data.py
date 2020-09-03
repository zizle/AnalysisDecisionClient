# _*_ coding:utf-8 _*_
# @File  : user_data.py
# @Time  : 2020-09-03 14:12
# @Author: zizle
import json
from datetime import datetime
from PyQt5.QtWidgets import qApp, QListWidgetItem
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from settings import SERVER_API, logger
from utils.client import get_user_token
from .user_data_ui import UserDataMaintainUI, SheetChartUI


class UserDataMaintain(UserDataMaintainUI):
    def __init__(self, *args, **kwargs):
        super(UserDataMaintain, self).__init__(*args, **kwargs)
        self.is_ready = False  # 左侧菜单选择时是否请求品种下的数据组

        for menu_item in [
            {"name": "数据源配置", "name_en": "source_config"},
            {"name": "品种数据表", "name_en": "variety_sheet"},
            {"name": "我的数据图", "name_en": "sheet_chart"},
        ]:
            menu = QListWidgetItem(menu_item["name"])
            menu.setData(Qt.UserRole, menu_item["name_en"])
            self.maintain_menu.addItem(menu)

        self.maintain_menu.clicked.connect(self.selected_maintain_menu)   # 选择操作菜单
        self.source_config_widget.confirm_group_button.clicked.connect(self.create_new_sheet_group)  # 确定新增分组
        # 数据源配置页品种选择变化信号连接(请求当前品种下的分组)
        self.source_config_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        # 数据表显示页品种选择变化信号连接放在请求完品种权限返回添加完数据之后(不在__init__内连接信号可以减少一次请求分组的网络)

        self._get_user_variety()  # 获取用户有权限的品种(置于信号连接之后确保首次信号执行)

    def _get_user_variety(self):
        """ 获取用户有权限的品种信息 """
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/variety-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_variety_reply)

    def user_variety_reply(self):
        """ 获取用户的品种权限返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            pass
        else:
            data = json.loads(data.decode("utf-8"))
            current_user = data.get("user")
            if not current_user:
                logger.error("登录过期了,用户获取有权限的品种失败!")
                return
            self._combobox_allow_varieties(data["varieties"])
        reply.deleteLater()

    def _combobox_allow_varieties(self, varieties):
        today_str = datetime.today().strftime("%Y-%m-%d")
        for variety_item in varieties:
            if not variety_item["expire_date"] or variety_item["expire_date"] <= today_str:
                continue
            # 数据源配置页
            self.source_config_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 数据表显示页
            self.variety_sheet_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 品种图形显示页
            self.sheet_chart_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])

        # 数据表显示页品种选择变化(不在__init__内连接信号可以减少一次网络请求)
        self.variety_sheet_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        self.is_ready = True

    def selected_maintain_menu(self):
        """ 选择了左侧菜单 """
        current_menu = self.maintain_menu.currentItem().data(Qt.UserRole)
        if current_menu == "source_config":
            self.maintain_frame.setCurrentIndex(0)
        elif current_menu == "variety_sheet":
            self.maintain_frame.setCurrentIndex(1)
        elif current_menu == "sheet_chart":
            self.maintain_frame.setCurrentIndex(2)
            return   # 图形界面无需再请求品种下的数据分组
        else:
            return
        if self.is_ready:
            self.variety_combobox_changed()  # 手动调用请求品种下的分组(否则第一次切换到品种表页面没有分组)

    def variety_combobox_changed(self):
        """ 界面品种变化 """
        current_widget = self.maintain_frame.currentWidget()
        current_variety = current_widget.variety_combobox.currentData()
        if isinstance(current_widget, SheetChartUI):
            return
        self.get_variety_sheet_group(current_variety)

    def create_new_sheet_group(self):
        """ 创建新的品种数据分组 """
        group_name = self.source_config_widget.new_group_edit.text().strip()

        current_variety = self.source_config_widget.variety_combobox.currentData()
        if not all([group_name, current_variety]):
            return
        user_token = get_user_token()
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, json.dumps({"group_name": group_name}).encode("utf-8"))
        reply.finished.connect(self.variety_sheet_group_reply)

    def get_variety_sheet_group(self, current_variety):
        """ 获取品种下的数据分组 """
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(request)
        reply.finished.connect(self.variety_sheet_group_reply)

    def variety_sheet_group_reply(self):
        """ 品种下的数据分组返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            logger.error("用户(新建时)获取数据分组失败:{}".format(data))
        else:
            self.source_config_widget.hide_create_new_group()
            current_widget = self.maintain_frame.currentWidget()
            data = json.loads(data.decode("utf-8"))
            current_widget.group_combobox.clear()
            current_widget.group_combobox.addItem("全部", 0)
            for group_item in data["groups"]:
                current_widget.group_combobox.addItem(group_item["group_name"], group_item["id"])
        reply.deleteLater()

