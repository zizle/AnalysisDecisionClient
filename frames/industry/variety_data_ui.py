# _*_ coding:utf-8 _*_
# @File  : variety_data_ui.py
# @Time  : 2020-09-03 8:29
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QMargins
from components.variety_tree import VarietyTree


class VarietyDataUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietyDataUI, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        main_splitter = QSplitter(self)

        self.variety_tree = VarietyTree()
        main_splitter.addWidget(self.variety_tree)

        self.web_container = QWebEngineView(self)
        main_splitter.addWidget(self.web_container)

        main_splitter.setStretchFactor(1, 4)
        main_splitter.setStretchFactor(2, 6)

        main_splitter.setHandleWidth(1)

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)
