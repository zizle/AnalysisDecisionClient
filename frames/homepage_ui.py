# _*_ coding:utf-8 _*_
# @File  : homepage_ui.py
# @Time  : 2020-07-19 15:12
# @Author: zizle
import os
from PyQt5.QtWidgets import (qApp, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QPushButton, QListWidget,
                             QStackedWidget, QGridLayout, QTableWidget, QFrame, QHeaderView, QTableWidgetItem,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QRect, QEasingCurve, QMargins, QSize, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QIcon, QImage, QFont, QBrush, QColor
from PyQt5.QtNetwork import QNetworkRequest
from widgets.sliding_stacked import SlidingStackedWidget
from utils.constant import HORIZONTAL_SCROLL_STYLE, VERTICAL_SCROLL_STYLE
from settings import STATIC_URL


class LeftChildrenMenuWidget(QWidget):
    """ 左侧子菜单的显示 """
    SelectedMenu = pyqtSignal(str, str)

    def __init__(self, menus, *args, **kwargs):
        super(LeftChildrenMenuWidget, self).__init__(*args, **kwargs)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.setContentsMargins(QMargins(10, 10, 10, 10))
        layout.setSpacing(10)
        # 增加button按钮
        row, col = 0, 0
        for menu_item in menus:
            button = QPushButton(menu_item["name"], self)
            setattr(button, "menu_id", menu_item["id"])
            button.setObjectName("pushButton")
            button.setFixedSize(110, 22)
            button.clicked.connect(self.menu_selected)
            layout.addWidget(button, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        self.setLayout(layout)

        self.setStyleSheet(
            "#pushButton{border:none;background-color:rgb(225,225,225)}"
            "#pushButton:hover{border:none;background-color:rgb(205,205,205)}"
        )

    def menu_selected(self):
        """ 菜单点击 """
        sender = self.sender()
        self.SelectedMenu.emit(getattr(sender, "menu_id"), sender.text())


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


""" 模块控件内的信息展示表格 """


class ModuleWidgetTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(ModuleWidgetTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QHeaderView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setObjectName("contentTable")
        self.setStyleSheet(
            "#contentTable::item:hover{color:rgb(248,121,27)}"
        )


""" 各模块控件 """


class ModuleWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(ModuleWidget, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground, True)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(1, 1, 1, 1))
        main_layout.setSpacing(0)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(QMargins(8, 0, 8, 0))
        title_layout.setAlignment(Qt.AlignVCenter)
        self.title_label = QLabel(self)
        self.title_label.setFixedHeight(40)  # 固定标题高度
        self.title_label.setObjectName("titleLabel")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.more_button = QPushButton("更多>>", self)
        self.more_button.setCursor(Qt.PointingHandCursor)
        title_layout.addWidget(self.more_button)
        main_layout.addLayout(title_layout)
        # 分割线
        h_line = QFrame(self)
        h_line.setLineWidth(2)
        h_line.setFrameStyle(QFrame.HLine | QFrame.Plain)
        h_line.setStyleSheet("color:rgb(228,228,228)")
        main_layout.addWidget(h_line)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(QMargins(8, 3, 8, 8))
        self.content_table = ModuleWidgetTable(self)
        content_layout.addWidget(self.content_table)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)
        self.more_button.setObjectName("moreButton")
        self.setStyleSheet(
            "#titleLabel{color:rgb(233,66,66);font-size:15px;font-weight:bold}"
            "#moreButton{border:none;font-size:12px;color:rgb(104,104,104)}"
            "#moreButton:hover{color:rgb(233,66,66)}"
        )

    def set_title(self, title: str):
        """ 设置标题 """
        self.title_label.setText(title)

    def set_contents(
            self, content_values, content_keys, data_keys, resize_cols, column_text_color: dict,
            zero_text_color: list, center_alignment_columns: list
    ):
        """
        设置内容
        :params:content_values 内容列表
        :params: content_keys  内容的key
        :params: data_keys 设置在首个item中的DataKeys
        :params: resize_cols 设置随内容大小的列
        :params: column_text_color 设置改变文字颜色的列
        :params: zero_text_color 根据比0大小设置颜色的列
        """
        self.content_table.clearContents()
        self.content_table.setRowCount(8)
        self.content_table.setColumnCount(len(content_keys))
        self.content_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.content_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for col in resize_cols:
            self.content_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(content_values):
            for col, col_key in enumerate(content_keys):
                item = QTableWidgetItem(str(row_item[col_key]))
                if col == 0:
                    item.setData(Qt.UserRole, {key: row_item[key] for key in data_keys})
                if col in column_text_color.keys():
                    item.setForeground(QBrush(column_text_color.get(col)))
                if col in zero_text_color:
                    # 将内容转数字与0比较大小
                    if int(row_item[col_key]) > 0:
                        color = QColor(203, 0, 0)
                    elif int(row_item[col_key]) < 0:
                        color = QColor(0, 124, 0)
                    else:
                        color = QColor(0, 0, 0)
                    item.setForeground(QBrush(color))
                if col in center_alignment_columns:
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter)
                self.content_table.setItem(row, col, item)




# 首页布局
#  ——————————————————————————————
# | 侧 |              |           |
# | 边 |    菜单      |    广告    |
# | 菜 |——————————————————————————
# | 单 |                           |
# |    |       模块方块展示         |
# |    |                           |
#  ————————————————————————————————


class HomepageUI(QScrollArea):
    """ 首页UI """
    CONTROL_LEFT_DISTANCE = 428

    def __init__(self, *args, **kwargs):
        super(HomepageUI, self).__init__(*args, **kwargs)
        self.container = QWidget(self)  # 全局控件(scrollArea的幕布)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 0))

        # 左侧的菜单列表控件
        self.left_menu = QListWidget(self)
        # 固定宽度
        self.left_menu.setFixedWidth(42)
        layout.addWidget(self.left_menu)
        # 左侧菜单对应的stackedWidget
        self.left_stacked = QStackedWidget(self)
        # 固定宽度
        self.left_stacked.setFixedSize(370, 300)   # 固定宽度,广告的高度

        right_layout = QVBoxLayout()
        menu_ad_layout = QHBoxLayout()  # 菜单与广告布局
        menu_ad_layout.addWidget(self.left_stacked)
        # 图片轮播控件
        self.slide_stacked = SlidingStackedWidget(self)
        # 广告图片的高度
        self.slide_stacked.setFixedHeight(300)
        self.slide_stacked.setMaximumWidth(745)
        # 在轮播控件上选择按钮
        self.control_widget = QWidget(self)
        self.control_widget.setFixedHeight(300)
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE, 0)
        control_layout = QVBoxLayout()
        control_layout.setAlignment(Qt.AlignVCenter)
        self.control_widget.setLayout(control_layout)

        menu_ad_layout.addWidget(self.slide_stacked)
        menu_ad_layout.addStretch()

        right_layout.addLayout(menu_ad_layout)

        # 其他模块
        modules_layout = QGridLayout()
        modules_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        modules_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 短信通
        self.instant_message_widget = ModuleWidget(self)
        self.instant_message_widget.setFixedSize(370, 300)
        self.instant_message_widget.setObjectName("moduleWidget")
        self.instant_message_widget.set_title("即时资讯")
        modules_layout.addWidget(self.instant_message_widget, 0, 0)

        # 现货报价
        self.spot_price_widget = ModuleWidget(self)
        self.spot_price_widget.setFixedSize(370, 300)
        self.spot_price_widget.setObjectName("moduleWidget")
        self.spot_price_widget.set_title("现货报价")
        modules_layout.addWidget(self.spot_price_widget, 0, 1)

        # 日报
        self.daily_report_widget = ModuleWidget(self)
        self.daily_report_widget.setFixedSize(370, 300)
        self.daily_report_widget.setObjectName("moduleWidget")
        self.daily_report_widget.set_title("收盘日评")
        modules_layout.addWidget(self.daily_report_widget, 0, 2)
        # 周报
        self.weekly_report_widget = ModuleWidget(self)
        self.weekly_report_widget.setFixedSize(370, 300)
        self.weekly_report_widget.setObjectName("moduleWidget")
        self.weekly_report_widget.set_title("研究周报")
        modules_layout.addWidget(self.weekly_report_widget, 1, 0)

        # 月季报告
        self.monthly_report_widget = ModuleWidget(self)
        self.monthly_report_widget.setFixedSize(370, 300)
        self.monthly_report_widget.setObjectName("moduleWidget")
        self.monthly_report_widget.set_title("月季报告")
        modules_layout.addWidget(self.monthly_report_widget, 1, 1)

        # 月季报告
        self.annual_report_widget = ModuleWidget(self)
        self.annual_report_widget.setFixedSize(370, 300)
        self.annual_report_widget.setObjectName("moduleWidget")
        self.annual_report_widget.set_title("年度报告")
        modules_layout.addWidget(self.annual_report_widget, 1, 2)

        right_layout.addLayout(modules_layout)

        layout.addLayout(right_layout)
        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.horizontalScrollBar().setStyleSheet(HORIZONTAL_SCROLL_STYLE)
        self.verticalScrollBar().setStyleSheet(VERTICAL_SCROLL_STYLE)
        self.left_menu.setObjectName("LeftMenuList")
        self.setStyleSheet(
            "#LeftMenuList{border:none;color:rgb(254,254,254);font-size:14px;"
            "background-color:rgb(233,26,46);outline:none;}"
            "#LeftMenuList::item{padding:5px 0 5px 0px}"
            "#LeftMenuList::item:selected{background-color:rgb(240,240,240);color:rgb(0,0,0);out-line:none}"
            "#moduleWidget{background-color:rgb(254,254,254);border:1px solid rgb(240,240,240)}"
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

