# _*_ coding:utf-8 _*_
# @File  : homepage_b.py
# @Time  : 2020-07-19 15:14
# @Author: zizle
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QPushButton, QScrollBar
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSettings, QUrl, QThread
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from .homepage_ui import HomepageUI, ControlButton
from settings import BASE_DIR, SERVER_API


class AdImageThread(QThread):
    """ 请求广告图片的线程 """
    def __init__(self, image_list, *args, **kwargs):
        super(AdImageThread, self).__init__(*args, **kwargs)

    def run(self):
        pass


class Homepage(HomepageUI):
    """ 首页业务 """
    def __init__(self, *args, **kwargs):
        super(Homepage, self).__init__(*args, **kwargs)
        self.control_buttons = list()
        self.add_images()
        self.slide_stacked.autoStart(msec=4000)
        self.slide_stacked.clicked_release.connect(self.image_widget_clicked)
        self.slide_stacked.currentChanged.connect(self.change_button_icon)  # 图片变化设置icon的背景
        # 滚动条的滚动移动相对于父窗口的控制button位置
        self.horizontalScrollBar().valueChanged.connect(self.horizontal_scroll_value_changed)
        self.verticalScrollBar().valueChanged.connect(self.vertical_scroll_value_changed)

    def horizontal_scroll_value_changed(self, value):
        """ 横向滚动条滚动事件 """
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE - value, 0 - self.verticalScrollBar().value())  # 移动控制控件

    def vertical_scroll_value_changed(self, value):
        """ 纵向滚动条滚动事件 """
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE - self.horizontalScrollBar().value(), 0 - value)

    def add_images(self):
        """ 添加轮播的图片信息 """
        # 获取广告信息
        self.control_buttons.clear()
        for index, name in enumerate(os.listdir('Data/Images')):
            label = QLabel(self.slide_stacked)
            label.setScaledContents(True)
            label.setPixmap(QPixmap('Data/Images/' + name))
            self.slide_stacked.addWidget(label)
            button = ControlButton("media/icons/empty_circle.png", "media/icons/full_circle.png", self.control_widget)
            if index == 0:
                button.setIcon(QIcon(button.hover_icon_path))
            setattr(button, "image_index", index)
            button.clicked.connect(self.skip_to_image)
            self.control_buttons.append(button)
            self.control_widget.layout().addWidget(button)

    def change_button_icon(self, current_index):
        """ 改变button的背景icon """
        for button in self.control_buttons:
            if getattr(button, "image_index") == current_index:
                button.setIcon(QIcon(button.hover_icon_path))
            else:
                button.setIcon(QIcon(button.icon_path))

    def image_widget_clicked(self):
        """ 点击了广告 """
        print(self.slide_stacked.currentWidget())

    def skip_to_image(self):
        """ 跳到指定广告 """
        target_index = getattr(self.sender(), "image_index")
        if target_index is not None:
            self.slide_stacked.setCurrentIndex(target_index)
            self.change_button_icon(target_index)

