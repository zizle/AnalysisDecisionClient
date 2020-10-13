# _*_ coding:utf-8 _*_
# @File  : homepage_b.py
# @Time  : 2020-07-19 15:14
# @Author: zizle
import webbrowser
import json
from PyQt5.QtWidgets import qApp
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl, QEventLoop
from PyQt5.QtNetwork import QNetworkRequest
from widgets.pdf_shower import PDFContentPopup
from popup.advertisement import TextPopup
from .homepage_ui import HomepageUI, ControlButton, PixMapLabel
from settings import SERVER_API, STATIC_URL


class Homepage(HomepageUI):
    """ 首页业务 """
    def __init__(self, *args, **kwargs):
        super(Homepage, self).__init__(*args, **kwargs)
        self.event_loop = QEventLoop(self)
        self.control_buttons = list()
        self.get_all_advertisement()
        # self.slide_stacked.autoStart(msec=4000)  # 自动开启得放置于填充图片之后,否则闪退
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

    def get_all_advertisement(self):
        """ 获取所有的广告信息 """
        url = SERVER_API + 'advertisement/'
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.get_advertisement_reply)
        self.event_loop.exec_()

    def get_advertisement_reply(self):
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_advertisement(data["advertisements"])
            self.event_loop.quit()  # 没使用同步无法加载出控制的按钮
        reply.deleteLater()

    def show_advertisement(self, advertisements):
        """ 显示所有的广告"""
        self.control_buttons.clear()
        for index, ad_item in enumerate(advertisements):
            label = PixMapLabel(ad_item, self.slide_stacked)  # 内置QThread访问图片
            self.slide_stacked.addWidget(label)
            button = ControlButton("media/icons/empty_circle.png", "media/icons/full_circle.png", self.control_widget)
            if index == 0:
                button.setIcon(QIcon(button.hover_icon_path))
            setattr(button, "image_index", index)
            button.clicked.connect(self.skip_to_image)
            self.control_buttons.append(button)
            self.control_widget.layout().addWidget(button)
        if advertisements:
            self.slide_stacked.autoStart(msec=4000)

    # def add_images(self):
    #     """ 添加轮播的图片信息（开发GUI测试代码） """
    #     # 获取广告信息
    #     self.control_buttons.clear()
    #     for index, name in enumerate(os.listdir('Data/Images')):
    #         label = QLabel(self.slide_stacked)
    #         label.setScaledContents(True)
    #         label.setPixmap(QPixmap('Data/Images/' + name))
    #         self.slide_stacked.addWidget(label)
    #         button = ControlButton("media/icons/empty_circle.png", "media/icons/full_circle.png", self.control_widget)
    #         if index == 0:
    #             button.setIcon(QIcon(button.hover_icon_path))
    #         setattr(button, "image_index", index)
    #         button.clicked.connect(self.skip_to_image)
    #         self.control_buttons.append(button)
    #         self.control_widget.layout().addWidget(button)

    def change_button_icon(self, current_index):
        """ 改变button的背景icon """
        for button in self.control_buttons:
            if getattr(button, "image_index") == current_index:
                button.setIcon(QIcon(button.hover_icon_path))
            else:
                button.setIcon(QIcon(button.icon_path))

    def image_widget_clicked(self):
        """ 点击了广告 """
        current_ad = self.slide_stacked.currentWidget()
        ad_data = current_ad.get_ad_data()
        # 根据ad_data显示出来广告响应
        ad_type = ad_data["ad_type"]
        if ad_type == "file":
            file_url = STATIC_URL + ad_data["filepath"]
            p = PDFContentPopup(file=file_url, title=ad_data["title"])
            p.exec_()
        elif ad_type == "web":
            webbrowser.open_new_tab(ad_data["web_url"])
        elif ad_type == "content":
            p = TextPopup(message=ad_data["content"])
            p.setWindowTitle(ad_data["title"])
            p.exec_()
        else:
            pass

    def skip_to_image(self):
        """ 跳到指定广告 """
        target_index = getattr(self.sender(), "image_index")
        if target_index is not None:
            self.slide_stacked.setCurrentIndex(target_index)
            self.change_button_icon(target_index)
