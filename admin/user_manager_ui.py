# _*_ coding:utf-8 _*_
# @File  : user_manager_ui.py
# @Time  : 2020-09-01 14:47
# @Author: zizle

from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QLabel, QComboBox, QPushButton, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QMargins, Qt


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
        self.show_user_table.setColumnCount(10)
        self.show_user_table.setHorizontalHeaderLabels(["ID", "用户名", "手机", "用户号", "邮箱", "角色", "状态", "品种权限", "登录权限", "备注"])
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
        self.addTab(QWidget(self), "测试页")