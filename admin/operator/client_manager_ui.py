# _*_ coding:utf-8 _*_
# @File  : client_manager_ui.py
# @Time  : 2020-09-10 17:42
# @Author: zizle
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QLineEdit,
                             QHeaderView)


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

        # uuid搜索
        self.uuid_edit = QLineEdit(self)
        self.uuid_edit.setPlaceholderText("在此输入客户端识别号")
        option_layout.addWidget(self.uuid_edit)

        # 信息
        self.network_message = QLabel(self)
        option_layout.addWidget(self.network_message)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)
        self.client_table = QTableWidget(self)
        self.client_table.verticalHeader().hide()
        self.client_table.setColumnCount(7)
        self.client_table.setHorizontalHeaderLabels(["编号", "加入时间", "名称", "识别号", "类型", "有效", "修改"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.client_table)
        self.setLayout(main_layout)
