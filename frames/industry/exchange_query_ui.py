# _*_ coding:utf-8 _*_
# @File  : exchange_query_ui.py
# @Time  : 2020-08-20 13:38
# @Author: zizle
# _*_ coding:utf-8 _*_
# @File  : exchange_query_ui.py
# @Time  : 2020-07-23 15:46
# @Author: zizle
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QDateEdit, QLabel, QTableWidget, QPushButton,
                             QSpinBox, QAbstractItemView, QFrame)
from PyQt5.QtCore import QDate, QMargins, Qt, QTime
from components.exchange_tree import ExchangeLibTree


class ExchangeQueryUI(QWidget):
    """ 查询数据之交易所数据UI """

    def __init__(self, *args, **kwargs):
        super(ExchangeQueryUI, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(2, 0, 2, 1))
        main_splitter = QSplitter(self)
        main_splitter.setHandleWidth(1)

        self.exchange_tree = ExchangeLibTree(self)

        main_splitter.addWidget(self.exchange_tree)

        self.show_widget = QWidget(self)
        show_layout = QVBoxLayout()
        show_layout.setContentsMargins(QMargins(2, 2, 0, 0))

        action_layout = QHBoxLayout()                       # 选择日期的layout
        action_layout.addWidget(QLabel("选择日期:", self))
        initialize_date = QDate.currentDate()
        if QTime.currentTime() < QTime(15, 50, 00):         # 小于15:50分时默认为前一天
            initialize_date = initialize_date.addDays(-1)
        while initialize_date.dayOfWeek() > 5:              # 当为周末时往前推日期
            initialize_date = initialize_date.addDays(-1)
        self.query_date_edit = QDateEdit(initialize_date, self)
        self.query_date_edit.setCalendarPopup(True)
        self.query_date_edit.setDisplayFormat("yyyy-MM-dd")
        action_layout.addWidget(self.query_date_edit)

        self.query_button = QPushButton("详情数据", self)
        self.query_button.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.query_button)

        self.rank_select = QSpinBox(self)
        self.rank_select.setMinimum(1)
        self.rank_select.setMaximum(20)
        self.rank_select.setValue(20)
        self.rank_select.setPrefix("前 ")
        self.rank_select.setSuffix(" 名")
        self.rank_select.hide()
        action_layout.addWidget(self.rank_select)

        self.query_variety_sum_button = QPushButton("品种合计", self)
        self.query_variety_sum_button.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.query_variety_sum_button)

        self.tip_label = QLabel("左侧选择想要查询的数据类别再进行查询.", self)
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.hide()
        action_layout.addWidget(self.tip_label)

        action_layout.addStretch()

        show_layout.addLayout(action_layout)

        self.show_table = QTableWidget(self)
        self.show_table.setEditTriggers(QAbstractItemView.NoEditTriggers)   # 不可编辑
        # self.show_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择为一行
        self.show_table.setFocusPolicy(Qt.NoFocus)                          # 去选中时的虚线框
        self.show_table.setAlternatingRowColors(True)                       # 交替行颜色
        self.show_table.horizontalHeader().setDefaultSectionSize(120)       # 默认的标题头宽
        self.show_table.verticalHeader().hide()                             # 隐藏列
        self.show_table.setFrameShape(QFrame.NoFrame)
        show_layout.addWidget(self.show_table)

        self.show_widget.setLayout(show_layout)

        main_splitter.addWidget(self.show_widget)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 7)

        layout.addWidget(main_splitter)

        self.setLayout(layout)
        self.tip_label.setObjectName("tipLabel")
        self.show_table.setObjectName("dataTable")
        self.show_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 #34adf3, stop: 0.5 #ccddff,stop: 0.6 #ccddff, stop:1 #34adf3);"
            "border:1px solid rgb(201,202,202);border-left:none;"
            "min-height:25px;min-width:30px;font-weight:bold;font-size:13px};"
        )
        self.show_table.verticalScrollBar().setStyleSheet(
            "QScrollBar:vertical{background: transparent; width:10px;margin: 0px;}"
            "QScrollBar:vertical:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:vertical{background: rgba(0,0,0,50);width:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:vertical:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-line:vertical{height:0px}"
            "QScrollBar::add-line:vertical{height:0px}"
        )
        self.show_table.horizontalScrollBar().setStyleSheet(
            "QScrollBar:horizontal{background:transparent;height:10px;margin:0px;}"
            "QScrollBar:horizontal:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:horizontal{background:rgba(0,0,0,50);height:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:horizontal:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-line:horizontal{width:0px}"
            "QScrollBar::add-line:horizontal{width:0px}"
        )
        self.setStyleSheet("#tipLabel{font-size:12x;font-weight:bold;color:rgb(230,50,50)}"
                           "#dataTable{selection-color:rgb(80,100,200);selection-background-color:rgb(220,220,220);alternate-background-color:rgb(245,250,248)}"
                           )
