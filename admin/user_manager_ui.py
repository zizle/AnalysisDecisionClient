# _*_ coding:utf-8 _*_
# @File  : user_manager_ui.py
# @Time  : 2020-09-01 14:47
# @Author: zizle

from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QLabel, QComboBox, QPushButton, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QMargins, Qt


class UserVarietyAuthUI(QWidget):
    """ 用户品种权限管理 """
    def __init__(self, *args, **kwargs):
        super(UserVarietyAuthUI, self).__init__(*args, **kwargs)
        self.current_user_id = None

        main_layout = QVBoxLayout()
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("当前用户:", self))
        self.current_username = QLabel(self)
        info_layout.addWidget(self.current_username)

        info_layout.addWidget(QLabel("用户号:", self))
        self.current_user_code = QLabel(self)
        info_layout.addWidget(self.current_user_code)

        info_layout.addStretch()

        main_layout.addLayout(info_layout)

        self.variety_auth_table = QTableWidget(self)
        main_layout.addWidget(self.variety_auth_table)

        self.setLayout(main_layout)


class UserClientAuthUI(QWidget):
    """ 用户客户端登录权限管理 """

    def __init__(self, *args, **kwargs):
        super(UserClientAuthUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()

        self.setLayout(main_layout)

class UserModuleAuthUI(QWidget):
    """ 用户客户端登录权限管理 """

    def __init__(self, *args, **kwargs):
        super(UserModuleAuthUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()

        self.setLayout(main_layout)


class UserListUI(QWidget):
    """ 用户列表 """

    def __init__(self, *args, **kwargs):
        super(UserListUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("角色:", self))
        self.user_role_combobox = QComboBox(self)
        for role_item in [
            {"name": "全部的用户", "role": "all"},
            {"name": "超级管理员", "role": "superuser"},
            {"name": "运营管理员", "role": "operator"},
            {"name": "信息管理员", "role": "collector"},
            {"name": "品种研究员", "role": "research"},
            {"name": "客户端用户", "role": "normal"},
        ]:
            self.user_role_combobox.addItem(role_item["name"], role_item["role"])
        options_layout.addWidget(self.user_role_combobox)

        self.query_button = QPushButton("查询", self)
        options_layout.addWidget(self.query_button)

        options_layout.addStretch()

        main_layout.addLayout(options_layout)

        self.show_user_table = QTableWidget(self)
        self.show_user_table.setFrameShape(QAbstractItemView.NoFrame)
        self.show_user_table.verticalHeader().hide()
        self.show_user_table.setColumnCount(11)
        self.show_user_table.setHorizontalHeaderLabels(
            ["ID", "用户名", "手机", "用户号", "邮箱", "角色", "状态", "登录权限", "模块权限", "品种权限", "备注"]
        )
        self.show_user_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.show_user_table)

        self.setLayout(main_layout)


class UserManagerUI(QTabWidget):
    """ 用户管理UI """

    def __init__(self, *args, **kwargs):
        super(UserManagerUI, self).__init__(*args, **kwargs)
        self.setTabPosition(QTabWidget.West)
        self.setTabShape(QTabWidget.Triangular)
        self.setDocumentMode(True)

        self.user_list_widget = UserListUI(self)
        self.addTab(self.user_list_widget, "用户列表")

        self.client_auth = UserClientAuthUI()

        self.module_auth = UserModuleAuthUI()

        self.variety_auth = UserVarietyAuthUI()

        self.setObjectName("userManagerTab")
        self.tabBar().setObjectName("tabBar")
        self.setStyleSheet(
            "#tabBar::tab{min-width:25px;}"
        )

