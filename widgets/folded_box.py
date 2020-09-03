# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
from math import floor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGridLayout, QScrollArea, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal


# 折叠盒子的按钮
class FoldedBodyButton(QPushButton):
    mouse_clicked = pyqtSignal(int, str)

    def __init__(self, text, bid, name_en=None, *args, **kwargs):
        super(FoldedBodyButton, self).__init__(*args, **kwargs)
        self.setText(text)
        self.bid = bid
        self.name_en = name_en
        self.clicked.connect(self.left_mouse_clicked)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName('button')

        self.setStyleSheet("""
        #button{
            border:none;
            padding: 5px 0;
            margin-top:3px;
            margin-bottom:3px;
            font-size: 13px;
            min-width: 70px;
            max-width: 70px;
        }
        #button:hover{
            color:rgb(200,120,200);
            background-color:rgb(200,200,200);
            background-color:rgb(200,200,200);
            border-radius:3px;
        }
        #button:pressed{
            background-color:rgb(150,150,180);
            color:rgb(250,250,250);
            border-radius:3px;
        }
        """)

    def left_mouse_clicked(self):
        # print(self.bid)
        name_en = self.name_en if self.name_en else ""
        self.mouse_clicked.emit(self.bid, name_en)


# FoldedHead(), FoldedBody()
# 折叠盒子的头
class FoldedHead(QWidget):
    def __init__(self, text, *args, **kwargs):
        super(FoldedHead, self).__init__(*args, **kwargs)
        self.head_text = text
        layout = QHBoxLayout(margin=0)
        self.head_label = QLabel(text, parent=self, objectName='headLabel')
        self.head_button = QPushButton('', parent=self, clicked=self.body_toggle, objectName='headButton', cursor=Qt.PointingHandCursor)
        self.head_button.setFixedSize(20, 20)
        layout.addWidget(self.head_label, alignment=Qt.AlignLeft)
        layout.addWidget(self.head_button, alignment=Qt.AlignRight)
        self.setLayout(layout)
        # 样式
        self.body_hidden = False  # 显示与否
        self.body_height = 0  # 原始高度
        # 样式
        self.setAutoFillBackground(True)  # 受父窗口影响(父窗口已设置透明)会透明,填充默认颜色
        self.setAttribute(Qt.WA_StyledBackground, True)  # 支持qss设置背景颜色(受父窗口透明影响qss会透明)

        self.moreButtonStyle()

    # 折叠的button样式
    def foldedButtonStyle(self):
        self.head_button.setStyleSheet("#headButton{border-image:url('media/folded.png')}")

    # 展开的button样式
    def moreButtonStyle(self):
        self.head_button.setStyleSheet("#headButton{border-image:url('media/more.png')}")

    # 设置身体控件(由于设置parent后用findChild没找到，用此法)
    def setBody(self, body):
        if not hasattr(self, 'bodyChild'):
            self.bodyChild = body

    def get_body(self):
        if hasattr(self, 'bodyChild'):
            return self.bodyChild
        return None

    # 窗体折叠展开动画
    def body_toggle(self):
        # print('头以下的身体折叠展开')
        body = self.get_body()
        if not body:
            return
        self.body_height = body.height()
        self.setMinimumWidth(self.width())
        if not self.body_hidden:
            body.hide()
            self.body_hidden = True
            self.foldedButtonStyle()
        else:
            body.show()
            self.body_hidden = False
            self.moreButtonStyle()


# 折叠盒子的身体
class FoldedBody(QWidget):
    mouse_clicked = pyqtSignal(int, str, str)

    def __init__(self, *args, **kwargs):
        super(FoldedBody, self).__init__(*args, **kwargs)
        layout = QGridLayout(margin=0)
        self.button_list = list()
        self.setLayout(layout)

    def addButton(self, id, name, name_en=None):
        button = FoldedBodyButton(text=name, bid=id, name_en=name_en, parent=self)
        button.mouse_clicked.connect(self.body_button_clicked)
        self.button_list.append(button)

    # 按钮被点击
    def body_button_clicked(self, bid, name_en):
        # 获取body的parent
        head = self.get_head()
        self.mouse_clicked.emit(bid, head.head_text, name_en)

    # 设置身体控件(由于设置parent后用findChild没找到，用此法)
    def setHead(self, head):
        if not hasattr(self, 'myHead'):
            self.myHead = head

    def get_head(self):
        if hasattr(self, 'myHead'):
            return self.myHead
        return None

    def resetHorizationItemCount(self, body_width):
        # 得到控件的大小，计算一列能容下的数量，向下取整
        horizontal_count = floor(body_width / 75)  # 根据button的宽度 + 间距5  来计算
        # 设置填入buttons
        row_index = 0
        col_index = 0
        for index, button in enumerate(self.button_list):
            self.layout().addWidget(button, row_index, col_index)
            col_index += 1
            if col_index == horizontal_count:  # 因为col_index先+1,此处应相等
                row_index += 1
                col_index = 0


# 滚动折叠盒子
class ScrollFoldedBox(QScrollArea):
    left_mouse_clicked = pyqtSignal(int, str, str)  # 当前id 与父级的text

    def __init__(self, *args, **kwargs):
        super(ScrollFoldedBox, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=0)
        self.container = QWidget(parent=self)
        self.container.setObjectName('foldedBox')
        self.container.setLayout(layout)
        self.setWidgetResizable(True)
        self.setWidget(self.container)
        # 设置样式
        self.setMinimumWidth(240)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.head_list = list()

    def setFoldedStyleSheet(self, stylesheet):
        self.setStyleSheet(stylesheet)

    # 添加头部
    def addHead(self, text):
        head = FoldedHead(text, parent=self.container, objectName='foldedHead')
        self.container.layout().addWidget(head, alignment=Qt.AlignTop)
        self.head_list.append(head)
        return head

    # 添加头部的身体
    def addBody(self, head):
        body = FoldedBody(parent=self.container, objectName='foldedBody')
        head.setBody(body)
        # 找出head所在的位置
        for i in range(self.container.layout().count()):
            widget = self.container.layout().itemAt(i).widget()
            if isinstance(widget, FoldedHead) and widget == head:
                self.container.layout().insertWidget(i + 1, body, alignment=Qt.AlignTop)
                break
        # 连接信号
        body.mouse_clicked.connect(self.left_mouse_clicked.emit)
        body.setHead(head)
        return body

    def setBodyHorizationItemCount(self):
        for head in self.head_list:
            body = head.get_body()
            if body:
                body.resetHorizationItemCount(self.width())