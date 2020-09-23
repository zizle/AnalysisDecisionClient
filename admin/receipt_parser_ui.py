# _*_ coding:utf-8 _*_
# @File  : receipt_parser_ui.py
# @Time  : 2020-09-23 14:43
# @Author: zizle
""" 仓单数据解析入库 """

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QPushButton, QLabel, QTableWidget
from PyQt5.QtCore import QDate, Qt


class ReceiptParserUI(QWidget):
    """ 仓单数据解析界面 """
    def __init__(self, *args, **kwargs):
        super(ReceiptParserUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()

        opt_layout = QHBoxLayout()
        self.current_date = QDateEdit(self)
        self.current_date.setDate(QDate.currentDate())
        self.current_date.setCalendarPopup(True)
        self.current_date.setDisplayFormat("yyyy-MM-dd")
        opt_layout.addWidget(self.current_date)

        self.parser_button = QPushButton("提取数据", self)
        opt_layout.addWidget(self.parser_button)

        self.message_label = QLabel("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取", self)
        opt_layout.addWidget(self.message_label)

        opt_layout.addStretch()
        main_layout.addLayout(opt_layout)

        self.preview_table = QTableWidget(self)
        main_layout.addWidget(self.preview_table)

        self.commit_button = QPushButton("提交保存", self)
        main_layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        self.setLayout(main_layout)