# _*_ coding:utf-8 _*_
# @File  : short_message_ui.py
# @Time  : 2020-09-18 15:48
# @Author: zizle

""" 短信通管理后台 """
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QScrollArea, QFrame
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QPalette


class ShortMessageAdminUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ShortMessageAdminUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        opt_layout.addWidget(self.date_edit)

        self.query_button = QPushButton("查询", self)
        opt_layout.addWidget(self.query_button)
        opt_layout.addStretch()

        main_layout.addLayout(opt_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)



