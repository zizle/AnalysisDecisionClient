# _*_ coding:utf-8 _*_
# @File  : client_manager_ui.py
# @Time  : 2020-09-10 17:42
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget


class ClientManageUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ClientManageUI, self).__init__(*args, *kwargs)
        main_layout = QVBoxLayout()
        option_layout = QHBoxLayout()
        option_layout.addWidget(QLabel("类型:", self))
        self.type_combobox = QComboBox(self)
        self.type_combobox.addItem("客户端", 0)
        self.type_combobox.addItem("管理端", 1)
        option_layout.addWidget(self.type_combobox)
        self.query_button = QPushButton("查询", self)
        option_layout.addWidget(self.query_button)
        option_layout.addStretch()
        main_layout.addLayout(option_layout)
        self.client_table = QTableWidget(self)
        main_layout.addWidget(self.client_table)
        self.setLayout(main_layout)
