# _*_ coding:utf-8 _*_
# @File  : net_position_ui.py
# @Time  : 2020-08-20 15:47
# @Author: zizle

""" 净持仓变化 """

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QFrame, QSpinBox, QPushButton, QLabel, QAbstractItemView
from PyQt5.QtCore import QMargins, Qt


class NetPositionUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(NetPositionUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(2, 1, 2, 1))
        main_layout.setSpacing(1)

        # 操作栏
        opt_layout = QHBoxLayout()
        self.interval_days = QSpinBox(self)
        self.interval_days.setMinimum(1)
        self.interval_days.setMaximum(30)
        self.interval_days.setValue(5)
        self.interval_days.setPrefix("日期间隔 ")
        self.interval_days.setSuffix(" 天")
        opt_layout.addWidget(self.interval_days)

        self.query_button = QPushButton('确定', self)
        opt_layout.addWidget(self.query_button)

        self.tip_label = QLabel('左侧可选择间隔天数,确定查询数据. ', self)
        opt_layout.addWidget(self.tip_label)

        opt_layout.addStretch()

        main_layout.addLayout(opt_layout)

        # 显示数据的表
        self.data_table = QTableWidget(self)
        self.data_table.setFrameShape(QFrame.NoFrame)
        self.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)   # 不可编辑
        # self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择为一行
        self.data_table.setFocusPolicy(Qt.NoFocus)                          # 去选中时的虚线框
        self.data_table.setAlternatingRowColors(True)                       # 交替行颜色
        self.data_table.horizontalHeader().setDefaultSectionSize(85)        # 默认的标题头宽
        self.data_table.verticalHeader().hide()
        self.data_table.verticalHeader().setDefaultSectionSize(18)          # 设置行高(与下行代码同时才生效)
        self.data_table.verticalHeader().setMinimumSectionSize(18)
        main_layout.addWidget(self.data_table)

        self.setLayout(main_layout)

        self.tip_label.setObjectName("tipLabel")
        self.data_table.setObjectName("dataTable")
        self.data_table.horizontalScrollBar().setStyleSheet(
            "QScrollBar{background:transparent;height:10px;}"
            "QScrollBar::handle{background:lightgray;border:0px solid transparent;border-radius:2px}"
            "QScrollBar:left-arrow:horizontal,QScrollBar::right-arrow:horizontal{width:0}"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:none}"
        )

        self.data_table.horizontalHeader().setStyleSheet("QHeaderView::section,"
                                                         "QTableCornerButton::section{height:25px;background-color:rgb(243,245,248);font-weight:bold;font-size:13px}")
        self.setStyleSheet(
            "#tipLabel{color:rgb(230,50,50);font-weight:bold;}"
            "#dataTable::item{padding:2px}"
            "#dataTable{selection-color:rgb(80,100,200);selection-background-color:rgb(220,220,220);alternate-background-color:rgb(245,250,248)}"
        )

