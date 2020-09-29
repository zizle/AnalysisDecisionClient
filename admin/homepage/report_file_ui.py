# _*_ coding:utf-8 _*_
# @File  : report_file_ui.py
# @Time  : 2020-09-29 15:40
# @Author: zizle

""" 日报，周报的后台处理 """

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QLabel, QComboBox, QPushButton, QTableWidget,
                             QHeaderView, QAbstractItemView)
from PyQt5.QtCore import QDate


class ReportFileAdminUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ReportFileAdminUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        option_layout = QHBoxLayout()

        option_layout.addWidget(QLabel("文件:", self))
        self.filename = QLabel("从表格选择文件", self)
        option_layout.addWidget(self.filename)

        option_layout.addWidget(QLabel("日期:", self))
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        option_layout.addWidget(self.date_edit)

        option_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        option_layout.addWidget(self.variety_combobox)

        option_layout.addWidget(QLabel("报告类型:", self))
        self.report_type = QComboBox(self)
        option_layout.addWidget(self.report_type)

        option_layout.addWidget(QLabel("关联品种:", self))
        self.relative_variety = QLabel("下拉框选择品种(多选)", self)
        option_layout.addWidget(self.relative_variety)

        self.clear_relative_button = QPushButton("清除", self)
        option_layout.addWidget(self.clear_relative_button)

        self.confirm_button = QPushButton("确定", self)
        option_layout.addWidget(self.confirm_button)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)

        self.file_table = QTableWidget(self)
        self.file_table.setColumnCount(7)
        self.file_table.verticalHeader().hide()
        self.file_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setHorizontalHeaderLabels(["序号", "文件名", "大小", "创建时间", "", "", ""])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        main_layout.addWidget(self.file_table)

        self.setLayout(main_layout)

        self.no_selected_file()
        self.no_relative_variety()

    def has_selected_file(self):
        self.filename.setStyleSheet("color:rgb(66,66,233);font-size:13px")

    def no_selected_file(self):
        self.filename.setStyleSheet("color:rgb(233,66,66);font-size:13px")

    def has_relative_variety(self):
        self.relative_variety.setStyleSheet("color:rgb(66,66,233);font-size:13px")

    def no_relative_variety(self):
        self.relative_variety.setStyleSheet("color:rgb(233,66,66);font-size:13px")