# _*_ coding:utf-8 _*_
# @File  : report_file_ui.py
# @Time  : 2020-09-29 15:40
# @Author: zizle

""" 日报，周报的后台处理 """

from PyQt5.QtWidgets import (QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QLabel, QComboBox, QPushButton,
                             QTableWidget, QHeaderView, QAbstractItemView, QLineEdit)
from PyQt5.QtCore import QDate, Qt
from widgets.path_edit import FilePathLineEdit


class ReportFileAdminUI(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(ReportFileAdminUI, self).__init__(*args, **kwargs)

        upload_widget = QWidget(self)

        main_layout = QVBoxLayout()
        local_file_layout = QHBoxLayout()

        local_file_layout.addWidget(QLabel('本地文件:', self))
        self.local_file_edit = FilePathLineEdit(self)
        self.local_file_edit.setPlaceholderText("点击选择本地文件进行上传")
        self.local_file_edit.setFixedWidth(600)
        local_file_layout.addWidget(self.local_file_edit)
        self.explain_label = QLabel("说明:[本地文件]或[网络文件]只能选择一种,相关信息共享。", self)
        self.explain_label.setStyleSheet("color:rgb(66,233,66)")
        local_file_layout.addWidget(self.explain_label)
        local_file_layout.addStretch()
        main_layout.addLayout(local_file_layout)

        network_file_layout = QHBoxLayout()
        network_file_layout.addWidget(QLabel('网络文件:', self))
        self.filename = QLabel("从表格选择文件", self)
        self.filename.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.filename.setAlignment(Qt.AlignLeft)
        self.filename.setFixedWidth(600)
        network_file_layout.addWidget(self.filename)
        self.explain_label = QLabel("说明:[本地文件]或[网络文件]只能选择一种,相关信息共享。", self)
        self.explain_label.setStyleSheet("color:rgb(66,233,66)")
        network_file_layout.addWidget(self.explain_label)
        network_file_layout.addStretch()
        main_layout.addLayout(network_file_layout)

        option_layout = QHBoxLayout()

        option_layout.addWidget(QLabel("报告日期:", self))
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        option_layout.addWidget(self.date_edit)

        option_layout.addWidget(QLabel("报告类型:", self))
        self.report_type = QComboBox(self)
        option_layout.addWidget(self.report_type)

        option_layout.addWidget(QLabel("备选品种:", self))
        self.variety_combobox = QComboBox(self)
        option_layout.addWidget(self.variety_combobox)

        option_layout.addWidget(QLabel("关联品种:", self))
        self.relative_variety = QLabel("下拉框选择品种(多选)", self)
        option_layout.addWidget(self.relative_variety)

        self.clear_relative_button = QPushButton("清除", self)
        option_layout.addWidget(self.clear_relative_button)

        self.rename_edit = QLineEdit(self)
        self.rename_edit.setPlaceholderText("重命名文件(无需重命名请留空),无需填后缀.")
        self.rename_edit.setFixedWidth(266)
        option_layout.addWidget(self.rename_edit)

        self.confirm_button = QPushButton("确定添加", self)
        option_layout.addWidget(self.confirm_button)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)

        self.file_table = QTableWidget(self)
        self.file_table.setColumnCount(7)
        self.file_table.verticalHeader().hide()
        self.file_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setHorizontalHeaderLabels(["序号", "文件名", "大小", "创建时间", "", "", ""])
        self.file_table.horizontalHeader().setDefaultSectionSize(55)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.file_table)

        upload_widget.setLayout(main_layout)

        self.addTab(upload_widget, "上传报告")

        # 管理报告
        manager_widget = QWidget(self)
        manager_layout = QVBoxLayout()
        manager_option_layout = QHBoxLayout()
        self.manager_date = QDateEdit(self)
        self.manager_date.setDate(QDate.currentDate())
        self.manager_date.setDisplayFormat("yyyy-MM-dd")
        self.manager_date.setCalendarPopup(True)
        manager_option_layout.addWidget(self.manager_date)

        manager_option_layout.addWidget(QLabel("报告类型:", self))
        self.manager_report_type = QComboBox(self)
        manager_option_layout.addWidget(self.manager_report_type)

        manager_option_layout.addWidget(QLabel("相关品种:", self))
        self.manager_variety_combobox = QComboBox(self)
        manager_option_layout.addWidget(self.manager_variety_combobox)
        manager_layout.addLayout(manager_option_layout)

        self.manager_query_button = QPushButton("查询", self)
        manager_option_layout.addWidget(self.manager_query_button)

        manager_option_layout.addStretch()

        self.manager_table = QTableWidget(self)
        self.manager_table.setColumnCount(7)
        self.manager_table.setHorizontalHeaderLabels(["日期", "关联品种", "报告类型", "报告名称", "", "是否公开", ""])
        self.manager_table.horizontalHeader().setDefaultSectionSize(80)
        self.manager_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        manager_layout.addWidget(self.manager_table)

        manager_widget.setLayout(manager_layout)

        self.addTab(manager_widget, "管理报告")

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