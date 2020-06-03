# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------

from .avatar import CAvatar
from .folded_box import ScrollFoldedBox
from .paginator import Paginator
from .pdf_shower import PDFContentPopup, PDFContentShower
from .path_edit import ImagePathLineEdit, FilePathLineEdit

from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtCore import Qt


# 承载模块内容的窗口
class LoadedPage(QStackedWidget):
    def __init__(self, *args, **kwargs):
        super(LoadedPage, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)  # 受父窗口影响(父窗口已设置透明)会透明,填充默认颜色
        self.setMouseTracking(True)
        self.setObjectName('pageContainer')
        self.setAttribute(Qt.WA_StyledBackground, True)  # 支持qss设置背景颜色(受父窗口透明影响qss会透明)
        self.setStyleSheet("""
        #pageContainer{
            border: 1px solid rgb(34,102,175);
            border-top:none;
            background-color:rgb(240, 240, 240);
        }
        """)

    # 鼠标移动事件
    def mouseMoveEvent(self, event, *args, **kwargs):
        event.accept()  # 接受事件,不传递到父控件

    def remove_borders(self):
        self.setStyleSheet("""
        #pageContainer{
            background-color:rgb(240, 240, 240);
            border: none;
        }
        """)

    # 清除所有控件
    def clear(self):
        widget = None
        for i in range(self.count()):
            widget = self.widget(i)
            self.removeWidget(widget)
            if widget:
                widget.deleteLater()
        del widget
