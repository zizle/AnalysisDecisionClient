# _*_ coding:utf-8 _*_
# @File  : variety_ui.py
# @Time  : 2020-08-10 13:41
# @Author: zizle

from PyQt5.QtWidgets import (QWidget, QSplitter, QListWidget, QTableWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout,
                             QLabel, QComboBox, QLineEdit)
from PyQt5.QtCore import QMargins


class VarietyOptionWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietyOptionWidget, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(1, 1, 1, 1))
        opts_layout = QHBoxLayout()
        opts_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        self.add_button = QPushButton("新建品种", self)
        opts_layout.addWidget(self.add_button)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # 新建品种的widget
        self.new_variety_widget = QWidget(self)
        add_layout = QGridLayout()
        add_layout.setContentsMargins(QMargins(100, 50, 100, 50))

        add_layout.addWidget(QLabel("所属类别:", self), 0, 0)
        self.belong_group = QComboBox(self)
        add_layout.addWidget(self.belong_group, 0, 1)

        add_layout.addWidget(QLabel("属交易所", self), 1, 0)
        self.belong_exchange = QComboBox(self)
        add_layout.addWidget(self.belong_exchange, 1, 1)

        add_layout.addWidget(QLabel("中文名称", self), 2, 0)
        self.zh_name = QLineEdit(self)
        add_layout.addWidget(self.zh_name, 2, 1)

        add_layout.addWidget(QLabel("交易代码", self), 3, 0)
        self.en_name = QLineEdit(self)
        add_layout.addWidget(self.en_name, 3, 1)

        self.commit_new_button = QPushButton("确定提交", self)
        add_layout.addWidget(self.commit_new_button, 4, 0, 1, 2)

        self.new_variety_widget.setLayout(add_layout)

        layout.addWidget(self.new_variety_widget)
        self.new_variety_widget.hide()  # 隐藏新建填写信息的界面

        self.variety_table = QTableWidget(self)
        layout.addWidget(self.variety_table)

        self.setLayout(layout)


class VarietyAdminUI(QSplitter):
    def __init__(self, *args, **kwargs):
        super(VarietyAdminUI, self).__init__(*args, **kwargs)
        self.group_list = QListWidget(self)  # 品种分组选项
        self.addWidget(self.group_list)

        self.opts_widget = VarietyOptionWidget(self)  # 操作窗口

        self.variety_table = self.opts_widget.variety_table

        self.addWidget(self.opts_widget)

        self.setStretchFactor(0, 2)
        self.setStretchFactor(1, 8)
        self.setHandleWidth(1)
