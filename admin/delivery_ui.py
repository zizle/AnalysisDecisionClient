# _*_ coding:utf-8 _*_
# @File  : delivery_ui.py
# @Time  : 2020-09-22 14:17
# @Author: zizle
from PyQt5.QtWidgets import (QWidget, QStackedWidget, QSplitter, QHBoxLayout, QListWidget, QVBoxLayout, QPushButton,
                             QLineEdit, QLabel, QTableWidget, QTabWidget, QGridLayout, QFrame)
from PyQt5.QtCore import QMargins, Qt


class WarehouseNumber(QWidget):
    """ 仓库编号管理窗口 """
    def __init__(self, *args, **kwargs):
        super(WarehouseNumber, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 1, 1, 1))
        opts_layout = QHBoxLayout()
        self.new_name = QLineEdit(self)
        self.new_name.setPlaceholderText("在此输入新仓库简称新增仓库")
        opts_layout.addWidget(self.new_name)

        self.new_button = QPushButton("确认", self)
        opts_layout.addWidget(self.new_button)

        self.message_label = QLabel(self)
        opts_layout.addWidget(self.message_label)

        main_layout.addLayout(opts_layout)

        # 显示的表格
        self.warehouse_number_table = QTableWidget(self)
        main_layout.addWidget(self.warehouse_number_table)

        self.setLayout(main_layout)


class WarehouseManagerUI(QTabWidget):
    """ 仓库管理界面 """
    def __init__(self, *args, **kwargs):
        super(WarehouseManagerUI, self).__init__(*args, **kwargs)

        # 所有仓库显示
        self.warehouse_table = QTableWidget(self)
        self.warehouse_table.setFrameShape(QFrame.NoFrame)
        self.addTab(self.warehouse_table, "所有仓库")
        # 新建仓库
        self.create_warehouse_widget = QWidget(self)
        edit_layout = QGridLayout(self)

        edit_layout.addWidget(QLabel('所在地区:', self), 0, 0)
        self.area_edit = QLineEdit(self)
        edit_layout.addWidget(self.area_edit, 0, 1)

        edit_layout.addWidget(QLabel('仓库名称:', self), 1, 0)
        self.name_edit = QLineEdit(self)
        edit_layout.addWidget(self.name_edit, 1, 1)

        edit_layout.addWidget(QLabel('仓库简称:', self), 2, 0)
        self.short_name_edit = QLineEdit(self)
        self.short_name_edit.setPlaceholderText('简称需与交易所公布的一致!')
        edit_layout.addWidget(self.short_name_edit, 2, 1)

        edit_layout.addWidget(QLabel('仓库地址:', self), 3, 0)
        self.addr_edit = QLineEdit(self)
        edit_layout.addWidget(self.addr_edit, 3, 1)

        edit_layout.addWidget(QLabel('到达站港:', self), 4, 0)
        self.arrived_edit = QLineEdit(self)
        self.arrived_edit.setPlaceholderText('若未知可留空')
        edit_layout.addWidget(self.arrived_edit, 4, 1)

        edit_layout.addWidget(QLabel('所在经度:', self), 5, 0)
        self.lng_edit = QLineEdit(self)
        edit_layout.addWidget(self.lng_edit, 5, 1)

        edit_layout.addWidget(QLabel('所在纬度:', self), 6, 0)
        self.lat_edit = QLineEdit(self)
        edit_layout.addWidget(self.lat_edit, 6, 1)

        self.commit_button = QPushButton('提交', self)
        edit_layout.addWidget(self.commit_button, 8, 1, alignment=Qt.AlignRight)
        self.create_warehouse_widget.setLayout(edit_layout)

        self.create_warehouse_widget.setMaximumHeight(300)

        self.addTab(self.create_warehouse_widget, "新建仓库")


class DeliveryAdminUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(DeliveryAdminUI, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        main_splitter = QSplitter(self)
        # 菜单列表
        self.menu_list = QListWidget(self)
        main_splitter.addWidget(self.menu_list)
        # 显示窗口
        self.stacked_frame = QStackedWidget(self)
        main_splitter.addWidget(self.stacked_frame)

        main_layout.addWidget(main_splitter)
        main_splitter.setSizes([self.width() * 0.2, self.width() * 0.7])
        main_splitter.setHandleWidth(1)
        self.setLayout(main_layout)
