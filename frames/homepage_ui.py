# _*_ coding:utf-8 _*_
# @File  : homepage_ui.py
# @Time  : 2020-07-19 15:12
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPixmap


class HomepageUI(QWidget):
    """ 首页UI """
    def __init__(self, *args, **kwargs):
        super(HomepageUI, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        label = QLabel("期货分析助手", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color:rgb(250,20,10);font-size:30px")
        layout.addWidget(label)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("media/home_bg.png"), QRect())

