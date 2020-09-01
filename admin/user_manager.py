# _*_ coding:utf-8 _*_
# @File  : user_manager.py
# @Time  : 2020-09-01 15:31
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QPushButton, QWidget
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, QSize
from settings import SERVER_API, logger
from utils.client import get_user_token
from .user_manager_ui import UserManagerUI


class UserManager(UserManagerUI):
    """ 用户管理业务逻辑 """
    ROLE_ZH = {
        "superuser": "超级管理员",
        "operator": "运营管理员",
        "collector": "信息管理员",
        "research": "品种研究员",
        "normal": "客户端用户"
    }

    def __init__(self, *args, **kwargs):
        super(UserManager, self).__init__(*args, **kwargs)
        self._get_current_role_users()


    def _get_current_role_users(self):
        """ 获取当前角色的用户 """
        current_role = self.user_list_widget.user_role_combobox.currentData()
        user_token = get_user_token()
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'all-users/?role={}'.format(current_role)
        print(url)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode('utf-8'))
        reply = network_manager.get(request)
        reply.finished.connect(self.get_users_reply)

    def get_users_reply(self):
        """ 获取用户返回了 """
        reply = self.sender()
        if reply.error():
            logger.error("获取用户列表失败:{}".format(reply.error()))
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()

        self.show_all_users(data["users"])

    def show_all_users(self, user_list):
        """ 显示所有的用户 """
        self.user_list_widget.show_user_table.clearContents()
        self.user_list_widget.show_user_table.setRowCount(len(user_list))
        for row, row_item in enumerate(user_list):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["username"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["phone"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["user_code"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(row_item["email"])
            item4.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 4, item4)

            item5 = QTableWidgetItem(self.ROLE_ZH.get(row_item["role"], "未知"))
            item5.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 5, item5)

            item6 = QTableWidgetItem()
            state, text = (Qt.Checked, '在职') if row_item["is_active"] else (Qt.Unchecked, '离职')
            item6.setCheckState(state)
            item6.setText(text)
            self.user_list_widget.show_user_table.setItem(row, 6, item6)
            item6.setTextAlignment(Qt.AlignCenter)

            variety_button = QPushButton("编辑", self)
            setattr(variety_button, "row_index", row)
            variety_button.clicked.connect(self.to_variety_authority)
            self.user_list_widget.show_user_table.setCellWidget(row, 7, variety_button)

            login_button = QPushButton("编辑", self)
            setattr(login_button, "row_index", row)
            login_button.clicked.connect(self.to_login_authority)
            self.user_list_widget.show_user_table.setCellWidget(row, 8, login_button)

            item9 = QTableWidgetItem(str(row_item["note"]))
            item9.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 9, item9)

    def to_variety_authority(self):
        """ 跳转品种权限页面 """
        tab_index = self.addTab(QWidget(self), "品种权限")
        self.setCurrentIndex(tab_index)

    def to_login_authority(self):
        """ 跳转登录页面 """
        tab_index = self.addTab(QWidget(self), "登录权限")
        self.setCurrentIndex(tab_index)
