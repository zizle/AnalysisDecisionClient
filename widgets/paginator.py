# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from PyQt5.QtCore import Qt, pyqtSignal


class Paginator(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, total_pages=1, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(margin=0)
        self.total_pages = total_pages
        self.current_page = 1
        self.home_button = QPushButton('首页', objectName='pageButton', cursor=Qt.PointingHandCursor, clicked=self.go_home_page)
        self.pre_button = QPushButton('上一页', objectName='pageButton', cursor=Qt.PointingHandCursor, clicked=self.go_pre_page)
        self.current_label = QLabel(objectName='pageLabel')
        self.current_label.setText(str(self.current_page) + '/' + str(self.total_pages))
        self.next_button = QPushButton('下一页', objectName='pageButton', cursor=Qt.PointingHandCursor, clicked=self.go_next_page)
        self.final_button = QPushButton('尾页', objectName='pageButton', cursor=Qt.PointingHandCursor, clicked=self.go_final_page)
        layout.addWidget(self.home_button)
        layout.addWidget(self.pre_button)
        layout.addWidget(self.current_label)
        layout.addWidget(self.next_button)
        layout.addWidget(self.final_button)
        self.setLayout(layout)
        self.setStyleSheet("""
        #pageButton{
            border:none;
            color:rgb(100,100,100);
            font-size:12px;
        }
        #pageButton:hover{
            border-bottom:1px solid rgb(95,95,95);
        }
        #pageLabel{
            color:rgb(100,100,100);
        }
        """)

    def get_current_page(self):
        return self.current_page

    # 设置外边距
    def setMargins(self, a, b, c, d):
        self.layout().setContentsMargins(a, b, c, d)

    # 清空页码
    def clearPages(self):
        self.current_page = self.total_pages = 1
        self.current_label.setText('1/1')

    # 设置总页数
    def setTotalPages(self, total_pages):
        self.total_pages = total_pages
        self.current_page = self.current_page
        self.setCurrentPageLable()

    # 设置当前页
    def setCurrentPageLable(self):
        self.current_label.setText(str(self.current_page) + '/' + str(self.total_pages))

    # 点击首页
    def go_home_page(self):
        if self.current_page == 1:
            return
        self.current_page = 1
        self.setCurrentPageLable()
        self.clicked.emit(self.current_page)

    # 点击尾页
    def go_final_page(self):
        if self.current_page == self.total_pages:
            return
        self.current_page = self.total_pages
        self.setCurrentPageLable()
        self.clicked.emit(self.current_page)

    # 点击上一页
    def go_pre_page(self):
        if self.current_page == 1:
            return
        self.current_page -= 1
        self.setCurrentPageLable()
        self.clicked.emit(self.current_page)

    # 点击下一页
    def go_next_page(self):
        if self.current_page == self.total_pages:
            return
        self.current_page += 1
        # print('下一页里',self.current_page)
        self.setCurrentPageLable()
        self.clicked.emit(self.current_page)