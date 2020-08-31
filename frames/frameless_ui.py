# _*_ coding:utf-8 _*_
# @File  : frameless_ui.py
# @Time  : 2020-08-28 10:16
# @Author: zizle

""" 主窗口无边框的UI """

from PyQt5.QtWidgets import (qApp, QHBoxLayout, QWidget, QMainWindow, QVBoxLayout, QDesktopWidget, QLabel, QPushButton,
                             QMenuBar)
from PyQt5.QtGui import QColor, QPen, QPainter, QPixmap, QFont, QIcon, QEnterEvent
from PyQt5.QtCore import Qt, QMargins, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager
from settings import TITLE_BAR_HEIGHT, NAVIGATION_BAR_HEIGHT, WINDOW_TITLE, SYSTEM_MENUS


class TitleBarUI(QWidget):
    """ 标题栏UI 包含一些窗口默认事件的处理 """
    def __init__(self, *args, **kwargs):
        super(TitleBarUI, self).__init__(*args, **kwargs)
        self._mouse_pos = None                  # 方向记录

        main_layout = QHBoxLayout()

        self.title_icon = QLabel(self)          # 图标
        self.title_icon.setPixmap(QPixmap("media/logo.png"))
        self.title_icon.setScaledContents(True)
        main_layout.addWidget(self.title_icon, alignment=Qt.AlignLeft)

        self.title_text = QLabel(WINDOW_TITLE, self)
        main_layout.addWidget(self.title_text, alignment=Qt.AlignLeft)

        main_layout.addStretch()                # 撑开按钮与标题图标的

        # 最大、小、隐藏按钮
        font = QFont()
        font.setFamily('Webdings')

        self.minimum_button = QPushButton('0', self)
        self.minimum_button.setFont(font)
        self.minimum_button.clicked.connect(self.window_shown_minimum)
        main_layout.addWidget(self.minimum_button, alignment=Qt.AlignRight | Qt.AlignTop)

        self.maximum_button = QPushButton('1', self)
        self.maximum_button.setFont(font)
        self.maximum_button.clicked.connect(self.window_shown_maximum)
        main_layout.addWidget(self.maximum_button, alignment=Qt.AlignRight | Qt.AlignTop)

        self.close_button = QPushButton('r', self)
        self.close_button.setFont(font)
        self.close_button.clicked.connect(self.window_closed)
        main_layout.addWidget(self.close_button, alignment=Qt.AlignRight | Qt.AlignTop)

        self.menu_bar_layout = QHBoxLayout()
        self.menu_bar = QMenuBar(self)

        main_layout.addLayout(self.menu_bar_layout)

        self.setLayout(main_layout)

        # 样式,相关属性,大小设置
        main_layout.setContentsMargins(QMargins(2, 0, 0, 0))
        main_layout.setSpacing(0)
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.title_icon.setFixedSize(TITLE_BAR_HEIGHT, TITLE_BAR_HEIGHT)
        self.title_icon.setMargin(4)
        self.title_text.setMargin(3)
        self.minimum_button.setFixedSize(TITLE_BAR_HEIGHT, TITLE_BAR_HEIGHT)
        self.maximum_button.setFixedSize(TITLE_BAR_HEIGHT, TITLE_BAR_HEIGHT)
        self.close_button.setFixedSize(TITLE_BAR_HEIGHT, TITLE_BAR_HEIGHT)
        self.minimum_button.setObjectName('minimumButton')
        self.maximum_button.setObjectName('maximumButton')
        self.close_button.setObjectName('closeButton')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName('titleBar')
        self.title_text.setObjectName('titleText')
        self.setStyleSheet(
            "#titleBar{background-color:rgb(34,102,175);border-top-left-radius:5px;border-top-right-radius:5px;}"
            "#titleText{color:rgb(245,245,245)}"
            "#minimumButton,#maximumButton{border:none;background-color:rgb(34,102,175);}"
            "#closeButton{border:none;background-color:rgb(34,102,175);border-top-right-radius:5px;}"
            "#minimumButton:hover,#maximumButton:hover{background-color:rgb(33,165,229)}"
            "#closeButton:hover{background-color:rgb(200,49,61);border-top-right-radius:5px;}"
            "#minimumButton:pressed,#maximumButton:pressed{background-color:rgb(37,39,41)}"
            "#closeButton:pressed{color:white;background-color:rgb(161,73,92);border-top-right-radius:5px;}"
        )

    # 鼠标双击
    def mouseDoubleClickEvent(self, event):
        self.window_shown_maximum()

    # 鼠标移动
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._mouse_pos:
            self.parent().move(self.mapToGlobal(event.pos() - self._mouse_pos))
        event.accept()  # 接受事件,不传递到父控件

    # 鼠标点击
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.pos()
        event.accept()  # 接受事件,不传递到父控件

    # 鼠标弹起
    def mouseReleaseEvent(self, event):
        """鼠标弹起事件"""
        self._mouse_pos = None
        event.accept()  # 接受事件,不传递到父控件

    def window_shown_minimum(self):
        """ 最小化 """
        self.parent().showMinimized()

    def window_shown_maximum(self):
        """ 最大化、还原 """
        if self.maximum_button.text() == '1':
            self.maximum_button.setText('2')
            self.parent().showMaximized()
        else:
            self.maximum_button.setText('1')
            self.parent().showNormal()

    def window_closed(self):
        """ 关闭窗口 """
        self.parent().close()


class NavigationBar(QWidget):
    """ 菜单栏UI 含用户登录栏 """
    menu_clicked = pyqtSignal(str, str)

    def __init__(self, *args, **kwargs):
        super(NavigationBar, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(2, 0, 0, 0))  # 左侧2px与centerWidget的border一致

        # 菜单栏
        self.menu_bar = QMenuBar(self)
        main_layout.addWidget(self.menu_bar, alignment=Qt.AlignLeft)

        main_layout.addStretch()

        # 用户信息栏
        self.user_bar = QWidget(self)
        user_bar_layout = QHBoxLayout()
        user_bar_layout.setContentsMargins(QMargins(0, 0, 8, 0))
        user_bar_layout.setSpacing(8)

        self.username_button = QPushButton("登录", self)
        setattr(self.username_button, 'is_logged', 0)
        user_bar_layout.addWidget(self.username_button)

        self.logout_button = QPushButton(self)
        self.logout_button.hide()
        user_bar_layout.addWidget(self.logout_button)

        self.user_bar.setLayout(user_bar_layout)
        main_layout.addWidget(self.user_bar)

        self.setLayout(main_layout)
        # 设置菜单
        self.set_menus(SYSTEM_MENUS)

        # 样式属性,大小等
        self.setFixedHeight(NAVIGATION_BAR_HEIGHT)
        self.logout_button.setFixedSize(NAVIGATION_BAR_HEIGHT-10, NAVIGATION_BAR_HEIGHT-10)
        self.username_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName('navigationBar')
        self.username_button.setObjectName("usernameButton")
        self.logout_button.setObjectName("logoutButton")
        self.menu_bar.setObjectName("menuBar")
        self.setStyleSheet(
            "#navigationBar{background-color:rgb(34,102,175)}"
            "#usernameButton{border:none;}"
            "#usernameButton:hover{border:none;color:rgb(255,255,255)}"
            "#logoutButton{border-image:url(media/icons/logout.png);}"
            "#logoutButton:hover{border-image:url(media/icons/logout_hover.png);}"
            "#menuBar{background-color:rgb(34,102,175);color:rgb(255,255,255)}"
            "#menuBar::item{background-color:rgb(34,102,175);border:1px solid rgb(34,142,155);padding:0 5px;margin:0 1px}"
            "#menuBar::item:selected{background-color:rgb(34,132,200);color:rgb(255,255,255)}"
            "#menuBar::item:pressed{background:rgb(34,142,175)}"
        )

    def set_menus(self, menu_data, parent_menu=None):
        """ 设置菜单 """
        for menu_item in menu_data:
            if menu_item["children"]:
                if parent_menu:
                    menu = parent_menu.addMenu(menu_item["name"])
                    menu.setIcon(QIcon(menu_item["logo"]))
                else:
                    menu = self.menu_bar.addMenu(menu_item["name"])
                    menu.setIcon(QIcon(menu_item["logo"]))
                menu.setObjectName("subMenu")
                self.set_menus(menu_item["children"], menu)
            else:
                if parent_menu:
                    action = parent_menu.addAction(menu_item["name"])
                    action.setIcon(QIcon(menu_item["logo"]))
                else:
                    action = self.menu_bar.addAction(menu_item["name"])
                    action.setIcon(QIcon(menu_item["logo"]))
                setattr(action, "id", menu_item['id'])
                action.triggered.connect(self.select_menu_action)

    def select_menu_action(self):
        action = self.sender()
        action_id = getattr(action, "id")
        action_text = action.text()
        self.menu_clicked.emit(action_id, action_text)

    def set_user_login_status(self, status):
        """ 设置用户的登录状态 """
        setattr(self.username_button, 'is_logged', status)


class FrameLessWindowUI(QWidget):
    """ 主窗口UI 无边框窗口的基本事件(放大缩小移动等)处理"""
    Left, Top, Right, Bottom, LeftTop, RightTop, LeftBottom, RightBottom = range(8)  # 枚举左上右下以及四个定点
    MARGIN = 5                                                                       # 边缘宽度小用于调整窗口大小

    def __init__(self, *args, **kwargs):
        super(FrameLessWindowUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN))
        main_layout.setSpacing(0)

        # 基本事件属性设置
        self.setMouseTracking(True)
        self._pressed = False
        self._direction = None
        self._mouse_pos = None

        self.title_bar = TitleBarUI(self)                                   # 窗口标题栏
        main_layout.addWidget(self.title_bar, alignment=Qt.AlignTop)

        self.navigation_bar = NavigationBar(self)                           # 菜单和用户状态栏
        main_layout.addWidget(self.navigation_bar, alignment=Qt.AlignTop)

        self.center_widget = QMainWindow()                              # 模块窗体显示窗口
        main_layout.addWidget(self.center_widget)

        self.setLayout(main_layout)

        # 样式,属性,大小设置
        self.title_bar.installEventFilter(self)                             # 安装事件过滤进入标题栏还原鼠标样式
        self.navigation_bar.installEventFilter(self)
        self.center_widget.installEventFilter(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        available_size = QDesktopWidget().availableGeometry()               # 用户的桌面信息,来改变自身窗体大小
        available_width, available_height = available_size.width(), available_size.height()
        self.resize(available_width * 0.75, available_height * 0.8)
        self.setMaximumSize(available_width, available_height)              # 最大为用户桌面大小
        self.setMinimumSize(available_width * 0.5, available_height * 0.5)  # 最小为用户桌面大小的一半
        self.setAttribute(Qt.WA_TranslucentBackground, True)                # 窗口透明
        self.center_widget.setAutoFillBackground(True)                      # 被窗口透明影响,自动填充
        self.center_widget.setObjectName("centerWidget")
        self.setStyleSheet(
            "#centerWidget{background-color:rgb(255,255,255);border:2px solid rgb(34,102,175);border-top:none;"
            "border-bottom-right-radius:5px;border-bottom-left-radius:5px}"
        )

    def eventFilter(self, obj, event):
        """ 事件过滤器, 用于解决鼠标进入其它控件后还原为标准鼠标样式 """
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
            self._direction = None  # 去除方向
            self._pressed = None  # 去除按下标记
        return super(FrameLessWindowUI, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        """ 鼠标按下 """
        super(FrameLessWindowUI, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.pos()
            self._pressed = True

    def mouseReleaseEvent(self, event):
        """ 鼠标弹起事件 """
        super(FrameLessWindowUI, self).mouseReleaseEvent(event)
        self._pressed = False
        self._direction = None

        # 鼠标移动事件(只有边框MARGIN大小范围有效果,因为其他的是其子控件)(会捕获子控件的鼠标按住移动的事件)

    def mouseMoveEvent(self, event):
        super(FrameLessWindowUI, self).mouseMoveEvent(event)
        pos = event.pos()
        pos_x, pos_y = pos.x(), pos.y()
        wm, hm = self.width() - self.MARGIN, self.height() - self.MARGIN
        # print(wm, hm)
        # 窗口最大无需事件
        if self.isMaximized() or self.isFullScreen():
            self._direction = None
            self.setCursor(Qt.ArrowCursor)
            return
        if event.buttons() == Qt.LeftButton and self._pressed:
            self.resize_window(pos)
        if pos_x <= self.MARGIN and pos_y <= self.MARGIN:
            # 左上角
            self._direction = self.LeftTop
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= pos_x <= self.width() and hm <= pos_y <= self.height():
            # 右下角
            self._direction = self.RightBottom
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= pos_x and pos_y <= self.MARGIN:
            # 右上角
            self._direction = self.RightTop
            self.setCursor(Qt.SizeBDiagCursor)
        elif pos_x <= self.MARGIN and hm <= pos_y:
            # 左下角
            self._direction = self.LeftBottom
            self.setCursor(Qt.SizeBDiagCursor)
        elif 0 <= pos_x <= self.MARGIN <= pos_y <= hm:
            # 左边
            self._direction = self.Left
            self.setCursor(Qt.SizeHorCursor)
        elif wm <= pos_x <= self.width() and self.MARGIN <= pos_y <= hm:
            # 右边
            self._direction = self.Right
            self.setCursor(Qt.SizeHorCursor)
        elif wm >= pos_x >= self.MARGIN >= pos_y >= 0:
            # 上面
            self._direction = self.Top
            self.setCursor(Qt.SizeVerCursor)
        elif self.MARGIN <= pos_x <= wm and hm <= pos_y <= self.height():
            # 下面
            self._direction = self.Bottom
            self.setCursor(Qt.SizeVerCursor)

    def paintEvent(self, event):
        """ 由于是全透明背景窗口,重绘事件中绘制透明度为1的难以发现的边框,用于调整窗口大小 """
        super(FrameLessWindowUI, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255, 1), self.MARGIN * 2))
        painter.drawRect(self.rect())

    def resize_window(self, pos):
        """ 调整窗口大小 """
        if self._direction is None:
            return
        mpos = pos - self._mouse_pos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()
        if self._direction == self.LeftTop:  # 左上角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
        elif self._direction == self.RightBottom:  # 右下角
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mouse_pos = pos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mouse_pos = pos
        elif self._direction == self.RightTop:  # 右上角
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mouse_pos.setX(pos.x())
        elif self._direction == self.LeftBottom:  # 左下角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mouse_pos.setY(pos.y())
        elif self._direction == self.Left:  # 左边
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return
        elif self._direction == self.Right:  # 右边
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mouse_pos = pos
            else:
                return
        elif self._direction == self.Top:  # 上面
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return
        elif self._direction == self.Bottom:  # 下面
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mouse_pos = pos
            else:
                return
        self.setGeometry(x, y, w, h)

    def showMaximized(self):
        """ 窗口最大化去除边界MARGIN """
        super(FrameLessWindowUI, self).showMaximized()
        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        """ 还原保留调整大小的边界 """
        super(FrameLessWindowUI, self).showNormal()
        self.layout().setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)

