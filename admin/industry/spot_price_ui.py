# _*_ coding:utf-8 _*_
# @File  : spot_price_ui.py
# @Time  : 2020-08-25 14:56
# @Author: zizle


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QDateEdit, QTabWidget
from PyQt5.QtCore import QDate


class SpotPriceAdminUI(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(SpotPriceAdminUI, self).__init__(*args, **kwargs)
        self.extra_data_widget = QWidget(self)
        # 提取数据tab
        layout = QVBoxLayout()
        # 现货价格源数据
        source_layout = QHBoxLayout()
        self.current_date = QDateEdit(self)
        self.current_date.setDisplayFormat("yyyy-MM-dd")
        self.current_date.setDate(QDate.currentDate())
        self.current_date.setCalendarPopup(True)
        source_layout.addWidget(self.current_date)

        source_layout.addWidget(QLabel("源数据:", self))
        self.source_edit = QLineEdit(self)
        source_layout.addWidget(self.source_edit)
        layout.addLayout(source_layout)
        # 分析
        analysis_layout = QHBoxLayout()
        self.analysis_button = QPushButton("提取数据", self)
        analysis_layout.addWidget(self.analysis_button)

        self.tip_label = QLabel("输入源数据后,点击提取数据进行数据提取.", self)
        analysis_layout.addWidget(self.tip_label)
        analysis_layout.addStretch()
        layout.addLayout(analysis_layout)

        # 预览数据的表格
        self.preview_table = QTableWidget(self)
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["日期", "品种", "交易代码", "现货价", "增减"])
        layout.addWidget(self.preview_table)

        # 提交按钮
        commit_layout = QHBoxLayout()
        commit_layout.addStretch()
        self.commit_button = QPushButton("确认提交", self)
        commit_layout.addWidget(self.commit_button)
        layout.addLayout(commit_layout)

        self.extra_data_widget.setLayout(layout)

        self.addTab(self.extra_data_widget, "数据提取")   # 提取数据tab

        # 修改数据的tab
        self.modify_data_widget = QWidget(self)
        modify_layout = QVBoxLayout()
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("选择日期:", self))
        self.modify_date_edit = QDateEdit(self)
        self.modify_date_edit.setDate(QDate.currentDate())
        self.modify_date_edit.setCalendarPopup(True)
        self.modify_date_edit.setDisplayFormat("yyyy-MM-dd")
        params_layout.addWidget(self.modify_date_edit)
        self.modify_query_button = QPushButton("查询", self)
        params_layout.addWidget(self.modify_query_button)
        self.modify_tip_label = QLabel("选择日期查询出数据,双击要修改的数据编辑正确的数据,点击行尾修改.", self)
        params_layout.addWidget(self.modify_tip_label)
        params_layout.addStretch()

        modify_layout.addLayout(params_layout)

        # 数据表格
        self.modify_table = QTableWidget(self)
        self.modify_table.setColumnCount(6)
        self.modify_table.setHorizontalHeaderLabels(["ID", "日期", "品种", "现货价", "增减", "修改"])
        modify_layout.addWidget(self.modify_table)

        self.modify_data_widget.setLayout(modify_layout)

        self.addTab(self.modify_data_widget, "修改数据")

        self.setStyleSheet(
            "#modifyButton{border:none;color:rgb(180,30,50)}#modifyButton:hover{color:rgb(20,50,160)}"
        )

