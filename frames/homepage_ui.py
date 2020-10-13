# _*_ coding:utf-8 _*_
# @File  : homepage_ui.py
# @Time  : 2020-07-19 15:12
# @Author: zizle
import os
from PyQt5.QtWidgets import qApp, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QPushButton
from PyQt5.QtCore import Qt, QRect, QEasingCurve, QMargins, QSize, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QIcon, QImage
from PyQt5.QtNetwork import QNetworkRequest
from widgets.sliding_stacked import SlidingStackedWidget
from settings import STATIC_URL


class AdImageThread(QThread):
    """ 请求广告图片的线程 """
    get_back_image = pyqtSignal(QImage)

    def __init__(self, image_url, *args, **kwargs):
        super(AdImageThread, self).__init__(*args, **kwargs)
        self.image_url = image_url

    def run(self):
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(self.image_url)))
        reply.finished.connect(self.image_reply)
        self.exec_()

    def image_reply(self):
        reply = self.sender()
        if reply.error():
            pass
        else:
            image = QImage.fromData(reply.readAll().data())
            self.get_back_image.emit(image)
        reply.deleteLater()
        self.quit()


class PixMapLabel(QLabel):
    """ 显示图片的label """
    def __init__(self, ad_data, *args, **kwargs):
        super(PixMapLabel, self).__init__(*args)
        self.ad_data = ad_data
        url = STATIC_URL + self.ad_data.get("image", '')
        # 无法在本控件内直接使用异步访问图片(可能是由于上一级QEventLoop影响)
        # 如果上一级不用QEventLoop则无法加载除控制的按钮
        self.image_thread = AdImageThread(url)
        self.image_thread.finished.connect(self.image_thread.deleteLater)
        self.image_thread.get_back_image.connect(self.fill_image_pixmap)
        self.image_thread.start()

    def fill_image_pixmap(self, image: QImage):
        self.setPixmap(QPixmap(image))
        self.setScaledContents(True)

    def get_ad_data(self):
        return self.ad_data


class ControlButton(QPushButton):
    """ 跳转轮播位置按钮 """
    def __init__(self, icon_path, hover_icon_path, *args):
        super(ControlButton, self).__init__(*args)
        self.icon_path = icon_path
        self.hover_icon_path = hover_icon_path
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(self.icon_path))
        self.setObjectName("controlButton")
        self.setStyleSheet(
            "#controlButton{border:none;}#controlButton:hover{color:#d81e06}"
            "#controlButton:focus{outline: none;} "
        )
        self.setIconSize(QSize(13, 13))

    # def enterEvent(self, *args, **kwargs):
    #     self.setIcon(QIcon(self.hover_icon_path))
    #
    # def leaveEvent(self, *args, **kwargs):
    #     self.setIcon(QIcon(self.icon_path))


class HomepageUI(QScrollArea):
    """ 首页UI """
    CONTROL_LEFT_DISTANCE = 428

    def __init__(self, *args, **kwargs):
        super(HomepageUI, self).__init__(*args, **kwargs)
        self.container = QWidget(self)  # 全局控件(scrollArea的幕布)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        ll = QLabel("左侧控件等", self)
        ll.setFixedWidth(420)
        layout.addWidget(ll)
        # 右侧广告及其他控件
        right_layout = QVBoxLayout()
        # 图片轮播控件
        self.slide_stacked = SlidingStackedWidget(self)
        # 广告图片的高度
        self.slide_stacked.setFixedHeight(400)
        # 在轮播控件上选择按钮
        self.control_widget = QWidget(self)
        self.control_widget.setFixedHeight(400)
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE, 0)
        control_layout = QVBoxLayout()
        control_layout.setAlignment(Qt.AlignVCenter)
        self.control_widget.setLayout(control_layout)

        right_layout.addWidget(self.slide_stacked)

        # 其他模块
        self.module_widgets = QWidget(self)
        right_layout.addWidget(self.module_widgets)
        layout.addLayout(right_layout)

        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.horizontalScrollBar().setStyleSheet(
            "QScrollBar:horizontal{background:transparent;height:10px;margin:0px;}"
            "QScrollBar:horizontal:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:horizontal{background:rgba(0,0,0,50);height:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:horizontal:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-line:horizontal{width:0px}"
            "QScrollBar::add-line:horizontal{width:0px}"
        )
        self.verticalScrollBar().setStyleSheet(
            "QScrollBar:vertical{background: transparent; width:10px;margin: 0px;}"
            "QScrollBar:vertical:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:vertical{background: rgba(0,0,0,50);width:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:vertical:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-line:vertical{height:0px}"
            "QScrollBar::add-line:vertical{height:0px}"
        )


class HomepageUI1(QWidget):
    """ 首页UI """
    def __init__(self, *args, **kwargs):
        super(HomepageUI1, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        label = QLabel("期货分析助手", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color:rgb(250,20,10);font-size:30px")
        layout.addWidget(label)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("media/home_bg.png"), QRect())

