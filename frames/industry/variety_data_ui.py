# _*_ coding:utf-8 _*_
# @File  : variety_data_ui.py
# @Time  : 2020-09-03 8:29
# @Author: zizle
from PyQt5.QtWidgets import (QWidget, QSplitter, QHBoxLayout, QTabWidget, QTableWidget, QFrame, QPushButton, QAbstractItemView,
                             QHeaderView)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QMargins, Qt
from components.variety_tree import VarietyTree


class OperateButton(QPushButton):
    """ 置顶按钮 """
    def __init__(self, icon_path, hover_icon_path, *args):
        super(OperateButton, self).__init__(*args)
        self.icon_path = icon_path
        self.hover_icon_path = hover_icon_path
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(self.icon_path))
        self.setObjectName("operateButton")
        self.setStyleSheet("#operateButton{border:none}#operateButton:hover{color:#d81e06}")

    def enterEvent(self, *args, **kwargs):
        self.setIcon(QIcon(self.hover_icon_path))

    def leaveEvent(self, *args, **kwargs):
        self.setIcon(QIcon(self.icon_path))


class VarietyDataUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietyDataUI, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        main_splitter = QSplitter(self)

        self.variety_tree = VarietyTree()
        main_splitter.addWidget(self.variety_tree)

        # 右侧Tab
        self.tab = QTabWidget(self)
        self.tab.setDocumentMode(True)
        self.tab.setTabShape(QTabWidget.Triangular)
        # 数据列表
        self.sheet_table = QTableWidget(self)
        self.sheet_table.setFrameShape(QFrame.NoFrame)
        self.sheet_table.setFocusPolicy(Qt.NoFocus)
        self.sheet_table.verticalHeader().hide()
        self.sheet_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.sheet_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sheet_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sheet_table.setAlternatingRowColors(True)

        self.sheet_table.setColumnCount(5)
        self.sheet_table.setHorizontalHeaderLabels(["序号", "标题", "数据起始", "数据结束", "图形"])
        self.sheet_table.verticalHeader().setDefaultSectionSize(25)  # 设置行高(与下行代码同时才生效)
        self.sheet_table.verticalHeader().setMinimumSectionSize(25)
        self.sheet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.sheet_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.sheet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # 图形列表
        self.chart_container = QWebEngineView(self)

        self.tab.addTab(self.chart_container, "图形库")
        self.tab.addTab(self.sheet_table, "数据库")

        main_splitter.addWidget(self.tab)

        main_splitter.setStretchFactor(1, 4)
        main_splitter.setStretchFactor(2, 6)

        main_splitter.setHandleWidth(1)

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        self.tab.tabBar().setObjectName("tabBar")
        self.sheet_table.setObjectName("sheetTable")
        self.sheet_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 #34adf3, stop: 0.5 #ccddff,stop: 0.6 #ccddff, stop:1 #34adf3);"
            "border:1px solid rgb(201,202,202);border-left:none;"
            "min-height:25px;min-width:40px;font-weight:bold;font-size:13px};"
        )
        self.setStyleSheet(
            "#tabBar::tab{min-height:20px;}"
            "#sheetTable{background-color:rgb(240,240,240);font-size:12px;"
            "selection-background-color:qlineargradient(x1:0,y1:0, x2:0, y2:1,"
            "stop:0 #cccccc,stop:0.5 white,stop:0.6 white,stop: 1 #cccccc);"
            "alternate-background-color:rgb(245,250,248);}"
        )
