# _*_ coding:utf-8 _*_
# @File  : user_extension_ui.py
# @Time  : 2020-09-16 13:30
# @Author: zizle
""" 用户拓展信息管理 """

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, QTableWidget,
                             QHeaderView)
from PyQt5.QtCore import QMargins

class UserExtensionUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(UserExtensionUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        option_layout = QHBoxLayout()
        option_layout.addWidget(QLabel("用户类型:", self))
        self.user_type_combobox = QComboBox(self)
        option_layout.addWidget(self.user_type_combobox)
        self.query_button = QPushButton("查询", self)
        option_layout.addWidget(self.query_button)
        self.phone_edit = QLineEdit(self)
        self.phone_edit.setPlaceholderText("在此输入手机号查询用户")
        option_layout.addWidget(self.phone_edit)

        self.message_label = QLabel(self)
        option_layout.addWidget(self.message_label)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)
        self.user_table = QTableWidget(self)
        self.user_table.verticalHeader().hide()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["编号", "手机", "微信ID", ""])
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.user_table)
        self.setLayout(main_layout)

        self.message_label.setObjectName("messageLabel")
        self.setStyleSheet(
            "#messageLabel{color:rgb(233,66,66)}"
        )
