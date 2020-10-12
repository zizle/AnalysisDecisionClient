# _*_ coding:utf-8 _*_
# @File  : homepage_ui.py
# @Time  : 2020-07-19 15:12
# @Author: zizle
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QPushButton
from PyQt5.QtCore import Qt, QRect, QEasingCurve, QMargins, QSize
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from widgets.sliding_stacked import SlidingStackedWidget


class ImageSliderWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super(ImageSliderWidget, self).__init__(*args, **kwargs)
        self.stacked_widget = SlidingStackedWidget(self)

        # self.setupUi(self)
        # # 初始化动画曲线类型
        # curve_types = [(n, c) for n, c in QEasingCurve.__dict__.items()
        #                if isinstance(c, QEasingCurve.Type)]
        # curve_types.sort(key=lambda ct: ct[1])
        # curve_types = [c[0] for c in curve_types]
        # self.comboBoxEasing.addItems(curve_types)

        # 绑定信号槽
        # self.spinBoxSpeed.valueChanged.connect(self.stackedWidget.setSpeed)
        # self.comboBoxEasing.currentTextChanged.connect(self.setEasing)
        # self.radioButtonHor.toggled.connect(self.setOrientation)
        # self.radioButtonVer.toggled.connect(self.setOrientation)
        # self.pushButtonPrev.clicked.connect(self.stackedWidget.slideInPrev)
        # self.pushButtonNext.clicked.connect(self.stackedWidget.slideInNext)
        # self.pushButtonStart.clicked.connect(self.autoStart)
        # self.pushButtonStop.clicked.connect(self.autoStop)

        # 添加图片页面
        for name in os.listdir('Data/Images'):
            label = QLabel(self.stackedWidget)
            label.setScaledContents(True)
            label.setPixmap(QPixmap('Data/Images/' + name))
            self.stackedWidget.addWidget(label)

    def autoStart(self):
        self.pushButtonNext.setEnabled(False)
        self.pushButtonPrev.setEnabled(False)
        self.stackedWidget.autoStart()

    def autoStop(self):
        self.pushButtonNext.setEnabled(True)
        self.pushButtonPrev.setEnabled(True)
        self.stackedWidget.autoStop()

    def setEasing(self, name):
        self.stackedWidget.setEasing(getattr(QEasingCurve, name))

    def setOrientation(self, checked):
        hor = self.sender() == self.radioButtonHor
        if checked:
            self.stackedWidget.setOrientation(
                Qt.Horizontal if hor else Qt.Vertical)


class ControlButton(QPushButton):
    """ 置顶按钮 """
    def __init__(self, icon_path, hover_icon_path, *args):
        super(ControlButton, self).__init__(*args)
        self.icon_path = icon_path
        self.hover_icon_path = hover_icon_path
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(self.icon_path))
        self.setObjectName("controlButton")
        self.setStyleSheet("#controlButton{border:none}#controlButton:hover{color:#d81e06}")
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



class HomepageUI2(QWidget):
    """ 首页UI """
    def __init__(self, *args, **kwargs):
        super(HomepageUI2, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        label = QLabel("期货分析助手", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color:rgb(250,20,10);font-size:30px")
        layout.addWidget(label)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("media/home_bg.png"), QRect())

