# _*_ coding:utf-8 _*_
# @File  : report_file_ui.py
# @Time  : 2020-09-29 15:40
# @Author: zizle

""" 日报，周报的后台处理 """

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QLabel, QComboBox, QPushButton, QTableWidget
from PyQt5.QtCore import QDate


class ReportFileAdminUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ReportFileAdminUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        option_layout = QHBoxLayout()

        option_layout.addWidget(QLabel("文件:", self))
        self.filename = QLabel(self)
        self.filename.setMinimumWidth(200)
        option_layout.addWidget(self.filename)

        option_layout.addWidget(QLabel("日期:", self))
        self.date_edit = QDateEdit(self)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        option_layout.addWidget(self.date_edit)

        option_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        option_layout.addWidget(self.variety_combobox)

        option_layout.addWidget(QLabel("报告类型:", self))
        self.report_type = QComboBox(self)
        option_layout.addWidget(self.report_type)

        self.confirm_button = QPushButton("确定", self)
        option_layout.addWidget(self.confirm_button)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)

        self.file_table = QTableWidget(self)
        self.file_table.setColumnCount(4)
        self.file_table.verticalHeader().hide()
        self.file_table.setHorizontalHeaderLabels(["序号", "文件名", "创建日期", ""])
        main_layout.addWidget(self.file_table)

        self.setLayout(main_layout)