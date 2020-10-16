# _*_ coding:utf-8 _*_
# @File  : product_ui.py
# @Time  : 2020-09-15 10:56
# @Author: zizle
""" 产品服务主界面 """

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QTabWidget, QTabBar, QMainWindow
from PyQt5.QtCore import Qt, QMargins
from widgets import ScrollFoldedBox


class ProductUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ProductUI, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        main_splitter = QSplitter(self)
        self.menu_folded = ScrollFoldedBox(self)
        main_splitter.addWidget(self.menu_folded)

        self.frame_tab = QMainWindow(self)

        main_splitter.addWidget(self.frame_tab)
        main_splitter.setHandleWidth(1)
        main_layout.addWidget(main_splitter)

        self.menu_folded.setMinimumWidth(180)
        self.menu_folded.setMaximumWidth(240)

        self.setLayout(main_layout)
        self.menu_folded.setFoldedStyleSheet(
            "QScrollArea{border: none;background-color:rgb(255,255,255)}"
            "#foldedBox{border-right: 1px solid rgb(180, 180, 180);}"
            "#foldedHead{background-color:rgb(1,129,135);border-bottom:1px solid rgb(200,200,200);"
            "border-right: 1px solid rgb(180, 180, 180);max-height: 30px;}"
            "#headLabel{padding:8px 5px;font-weight: bold;font-size: 15px;color:rgb(245,245,245);}"
            "#foldedBody{border-right: 1px solid rgb(180, 180, 180);}"
            "#foldedBox QScrollBar:vertical{width: 5px;background: transparent;}"
            "#foldedBox QScrollBar::handle:vertical {background: rgba(0, 0, 0, 30);width:5px;"
            "border-radius: 5px;border:none;}"
            "#foldedBox QScrollBar::handle:vertical:hover,"
            "QScrollBar::handle:horizontal:hover{background: rgba(0, 0, 0, 80);}"
        )

