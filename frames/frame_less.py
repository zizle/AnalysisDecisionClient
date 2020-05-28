# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-
# ---------------------------
import os
import shutil
from PyQt5.QtWidgets import qApp, QWidget, QDesktopWidget, QVBoxLayout, QLabel, QStackedWidget, QHBoxLayout, QPushButton, QMenu
from PyQt5.QtGui import QIcon, QEnterEvent, QPen, QPainter, QColor, QPixmap, QFont, QImage, QPainterPath, QMovie
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation, QRectF, QPointF, pyqtProperty, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache, QNetworkRequest
from widgets import LoadedPage
import settings


class CAvatar(QWidget):
    Circle = 0              # 圆圈
    Rectangle = 1           # 圆角矩形
    SizeLarge = QSize(128, 128)
    SizeMedium = QSize(64, 64)
    SizeSmall = QSize(32, 32)
    StartAngle = 0          # 起始旋转角度
    EndAngle = 360          # 结束旋转角度
    clicked = pyqtSignal(bool)

    def __init__(self, *args, shape=0, url='', cacheDir=False, size=QSize(64, 64), animation=False, **kwargs):
        super(CAvatar, self).__init__(*args, **kwargs)
        self.url = ''
        self._angle = 0             # 角度
        self.pradius = 0            # 加载进度条半径
        self.animation = animation  # 是否使用动画
        self._movie = None          # 动态图
        self._pixmap = QPixmap()    # 图片对象
        self.pixmap = QPixmap()     # 被绘制的对象
        self.isGif = url.endswith('.gif')
        # 进度动画定时器
        self.loadingTimer = QTimer(self, timeout=self.onLoading)
        # 旋转动画
        self.rotateAnimation = QPropertyAnimation(
            self, b'angle', self, loopCount=1)
        self.setShape(shape)
        self.setCacheDir(cacheDir)
        self.setSize(size)
        self.setUrl(url)

    def paintEvent(self, event):
        super(CAvatar, self).paintEvent(event)
        # 画笔
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # 绘制
        path = QPainterPath()
        diameter = min(self.width(), self.height())
        if self.shape == self.Circle:
            radius = int(diameter / 2)
        elif self.shape == self.Rectangle:
            radius = 4
        halfW = self.width() / 2
        halfH = self.height() / 2
        painter.translate(halfW, halfH)
        path.addRoundedRect(
            QRectF(-halfW, -halfH, diameter, diameter), radius, radius)
        painter.setClipPath(path)
        # 如果是动画效果
        if self.rotateAnimation.state() == QPropertyAnimation.Running:
            painter.rotate(self._angle)  # 旋转
            painter.drawPixmap(
                QPointF(-self.pixmap.width() / 2, -self.pixmap.height() / 2), self.pixmap)
        else:
            painter.drawPixmap(-int(halfW), -int(halfH), self.pixmap)
        # 如果在加载
        if self.loadingTimer.isActive():
            diameter = 2 * self.pradius
            painter.setBrush(
                QColor(45, 140, 240, (1 - self.pradius / 10) * 255))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                QRectF(-self.pradius, -self.pradius, diameter, diameter), self.pradius, self.pradius)

    def enterEvent(self, event):
        """鼠标进入动画
        :param event:
        """
        if not (self.animation and not self.isGif):
            return
        self.rotateAnimation.stop()
        cv = self.rotateAnimation.currentValue() or self.StartAngle
        self.rotateAnimation.setDuration(
            540 if cv == 0 else int(cv / self.EndAngle * 540))
        self.rotateAnimation.setStartValue(cv)
        self.rotateAnimation.setEndValue(self.EndAngle)
        self.rotateAnimation.start()

    def leaveEvent(self, event):
        """鼠标离开动画
        :param event:
        """
        if not (self.animation and not self.isGif):
            return
        self.rotateAnimation.stop()
        cv = self.rotateAnimation.currentValue() or self.EndAngle
        self.rotateAnimation.setDuration(int(cv / self.EndAngle * 540))
        self.rotateAnimation.setStartValue(cv)
        self.rotateAnimation.setEndValue(self.StartAngle)
        self.rotateAnimation.start()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.clicked.emit(True)

    def onLoading(self):
        """更新进度动画
        """
        if self.loadingTimer.isActive():
            if self.pradius > 9:
                self.pradius = 0
            self.pradius += 1
        else:
            self.pradius = 0
        self.update()

    def onFinished(self):
        """图片下载完成
        """
        self.loadingTimer.stop()
        self.pradius = 0
        reply = self.sender()
        if self.isGif:
            self._movie = QMovie(reply, b'gif', self)
            if self._movie.isValid():
                self._movie.frameChanged.connect(self._resizeGifPixmap)
                self._movie.start()
        else:
            data = reply.readAll().data()
            reply.deleteLater()
            del reply
            self._pixmap.loadFromData(data)
            if self._pixmap.isNull():
                self._pixmap = QPixmap(self.size())
                self._pixmap.fill(QColor(204, 204, 204))
            self._resizePixmap()

    def onError(self, code):
        """下载出错了
        :param code:
        """
        self._pixmap = QPixmap(self.size())
        self._pixmap.fill(QColor(204, 204, 204))
        self._resizePixmap()

    def refresh(self):
        """强制刷新
        """
        self._get(self.url)

    def isLoading(self):
        """判断是否正在加载
        """
        return self.loadingTimer.isActive()

    def setShape(self, shape):
        """设置形状
        :param shape:        0=圆形, 1=圆角矩形
        """
        self.shape = shape

    def setUrl(self, url):
        """设置url,可以是本地路径,也可以是网络地址
        :param url:
        """
        self.url = url
        # print('设置头像', url)
        self._get(url)

    def setCacheDir(self, cacheDir=''):
        """设置本地缓存路径
        :param cacheDir:
        """
        self.cacheDir = cacheDir
        self._initNetWork()

    def setSize(self, size):
        """设置固定尺寸
        :param size:
        """
        if not isinstance(size, QSize):
            size = self.SizeMedium
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self._resizePixmap()

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def _resizePixmap(self):
        """缩放图片
        """
        if not self._pixmap.isNull():
            self.pixmap = self._pixmap.scaled(
                self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.update()

    def _resizeGifPixmap(self, _):
        """缩放动画图片
        """
        if self._movie:
            self.pixmap = self._movie.currentPixmap().scaled(
                self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.update()

    def _initNetWork(self):
        """初始化异步网络库
        """
        if not hasattr(qApp, '_network'):
            network = QNetworkAccessManager(self.window())
            setattr(qApp, '_network', network)
        # 是否需要设置缓存
        if self.cacheDir and not qApp._network.cache():
            cache = QNetworkDiskCache(self.window())
            cache.setCacheDirectory(self.cacheDir)
            qApp._network.setCache(cache)

    def _get(self, url):
        """设置图片或者请求网络图片
        :param url:
        """
        if not url:
            self.onError('')
            return
        if url.startswith('http') and not self.loadingTimer.isActive():
            url = QUrl(url)
            request = QNetworkRequest(url)
            # request.setHeader(QNetworkRequest.UserAgentHeader, b'CAvatar')
            # request.setRawHeader(b'Author', b'Irony')
            request.setAttribute(
                QNetworkRequest.FollowRedirectsAttribute, True)
            if qApp._network.cache():
                request.setAttribute(
                    QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferNetwork)
                request.setAttribute(
                    QNetworkRequest.CacheSaveControlAttribute, True)
            reply = qApp._network.get(request)
            self.pradius = 0
            self.loadingTimer.start(50)  # 显示进度动画
            reply.finished.connect(self.onFinished)
            reply.error.connect(self.onError)
            return
        self.pradius = 0
        if os.path.exists(url) and os.path.isfile(url):
            if self.isGif:
                self._movie = QMovie(url, parent=self)
                if self._movie.isValid():
                    self._movie.frameChanged.connect(self._resizeGifPixmap)
                    self._movie.start()
            else:
                self._pixmap = QPixmap(url)
                self._resizePixmap()
        else:
            self.onError('')


# 标题栏
class TitleBar(QWidget):
    HEIGHT = settings.TITLE_BAR_HEIGHT

    def __init__(self, *args, **kwargs):
        super(TitleBar, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(margin=0, spacing=0)
        # 图标
        self.window_icon = QLabel(parent=self)
        pixmap = QPixmap('media/logo.png')
        self.window_icon.setScaledContents(True)
        self.window_icon.setPixmap(pixmap)
        # 标题
        self.window_title = QLabel(parent=self, objectName='titleName')
        layout.addWidget(self.window_icon, Qt.AlignLeft)
        layout.addWidget(self.window_title, Qt.AlignLeft)
        # 中间伸缩
        # layout.addStretch()
        # 右侧控制大小
        # 利用Webdings字体来显示图标
        font = QFont()
        font.setFamily('Webdings')
        # 最小化按钮
        self.buttonMinimum = QPushButton(
            '0', parent=self, font=font, clicked=self.windowMinimumed, objectName='buttonMinimum')
        layout.addWidget(self.buttonMinimum, alignment=Qt.AlignRight | Qt.AlignTop)
        # 最大化/还原按钮
        self.buttonMaximum = QPushButton(
            '1', parent=self, font=font, clicked=self.windowMaximized, objectName='buttonMaximum')
        layout.addWidget(self.buttonMaximum, alignment=Qt.AlignRight | Qt.AlignTop)
        # 关闭按钮
        self.buttonClose = QPushButton(
            'r', parent=self, font=font, clicked=self.windowClosed, objectName='buttonClose')
        layout.addWidget(self.buttonClose, alignment=Qt.AlignRight | Qt.AlignTop)
        # 属性、样式
        self._mouse_pos = None
        self.setObjectName('titleBar')
        self.setFixedHeight(self.HEIGHT)
        self.setAutoFillBackground(True)  # 受父窗口影响(父窗口已设置透明)会透明,填充默认颜色
        self.setAttribute(Qt.WA_StyledBackground, True)  # 支持qss设置背景颜色(受父窗口透明影响qss会透明)
        self.window_icon.setMargin(2)
        self.window_icon.setFixedSize(self.HEIGHT - 5, self.HEIGHT - 5)
        self.window_title.setMargin(3)
        self.buttonMinimum.setFixedSize(self.HEIGHT - 5, self.HEIGHT - 5)
        self.buttonMaximum.setFixedSize(self.HEIGHT - 5, self.HEIGHT - 5)
        self.buttonClose.setFixedSize(self.HEIGHT - 5, self.HEIGHT - 5)
        self.window_title.setText('瑞达期货研究院分析决策系统管理端')
        self.setStyleSheet("""
        #titleBar{
            background-color: rgb(34,102,175);
        }
        #titleName{
            color: rgb(210,210,210);
            font-size:14px;
            font-weight: bold;
        }
        /*最小化最大化关闭按钮通用默认背景*/
        #buttonMinimum,#buttonMaximum,#buttonClose {
            border: none;
            background-color: rgb(34,102,175);
        }

        /*悬停*/
        #buttonMinimum:hover,#buttonMaximum:hover {
            background-color: rgb(33,165,229);
        }
        #buttonClose:hover {
            color: white;
            background-color: rgb(200,49,61);
        }

        /*鼠标按下不放*/
        #buttonMinimum:pressed,#buttonMaximum:pressed {
            background-color: rgb(37,39,41);
        }
        #buttonClose:pressed {
            color: white;
            background-color: rgb(161, 73, 92);
        }

        """)

        # 布局
        self.setLayout(layout)

    # 最小化
    def windowMinimumed(self):
        # print('最小化窗口')
        self.parent().showMinimized()

    # 最大化
    def windowMaximized(self):
        # print('最大化窗口')
        if self.buttonMaximum.text() == '1':
            # 最大化
            self.buttonMaximum.setText('2')
            self.parent().showMaximized()
            # 修改配置中可用窗口显示区域的大小
            self.resize_access_frame_size()

        else:  # 还原
            self.buttonMaximum.setText('1')
            self.parent().showNormal()
            # 修改配置中可用窗口显示区域的大小
            self.resize_access_frame_size()

    # 调整可用显示区的大小
    def resize_access_frame_size(self):
        height = self.parent().height() - settings.TITLE_BAR_HEIGHT - settings.NAVIGATION_BAR_HEIGHT
        settings.app_dawn.setValue('SCREEN_WIDTH', self.parent().width() - 6)
        settings.app_dawn.setValue('SCREEN_HEIGHT', height)

    # 关闭
    def windowClosed(self):
        # print('关闭窗口')
        self.parent().close()

    # 鼠标双击
    def mouseDoubleClickEvent(self, event):
        self.windowMaximized()

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


""" 导航栏相关 """


# 自定义模块菜单的QPushButton
class ModuleButton(QPushButton):
    clicked_module = pyqtSignal(QPushButton)

    def __init__(self, mid, text, *args, **kwargs):
        super(ModuleButton, self).__init__(text, *args, **kwargs)
        self.mid = mid
        self.clicked.connect(lambda: self.clicked_module.emit(self))


# 管理菜单按钮
class DropdownMenu(QMenu):
    def __init__(self, *args, **kwargs):
        super(DropdownMenu, self).__init__(*args, **kwargs)
        self.setStyleSheet("""
        QMenu{
            background-color:rgb(34,102,175); /* sets background of the menu 设置整个菜单区域的背景色 */
            border: 1px solid rgb(250,255,250);/*整个菜单区域的边框粗细、样式、颜色*/
         }
        QMenu::item {
            /* sets background of menu item. set this to something non-transparent
                if you want menu color and menu item color to be different */
            background-color: transparent;
            padding:2px 16px;/*设置菜单项文字上下和左右的内边距，效果就是菜单中的条目左右上下有了间隔*/
            margin:0px 2px;/*设置菜单项的外边距*/
            border-bottom:1px solid rgb(180,255,250);/*为菜单项之间添加横线间隔*/
            color: rgb(255,255,255)
        }

        QMenu::item:selected { /* when user selects item using mouse or keyboard */
            background-color: #2dabf9;/*这一句是设置菜单项鼠标经过选中的样式*/
        }
        """)


# 模块菜单栏
class ModuleBar(QWidget):
    menu_clicked = pyqtSignal(int, str)

    def __init__(self, *args, **kwargs):
        super(ModuleBar, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(margin=0, spacing=0)
        self.setLayout(layout)
        # 样式设计
        self.setObjectName('moduleBar')
        self.setStyleSheet("""
        #moduleBar{
            min-height:24px;
            max-height:24px;
        }
        QPushButton{
            background-color:rgb(34,102,175);
            color: rgb(235,20,150);
            border: 1px solid rgb(34,142,155);
            margin-left:3px;
            padding: 1px 6px;  /*上下，左右*/
            min-height:16px;
            max-height:16px;
            color: #FFFFFF
        }
        QPushButton:hover {
            background-color: rgb(34,132,200);
        }
        """)
        self.set_default_menu()

    def clear(self):
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()
            del widget
        self.set_default_menu()

    def set_default_menu(self):
        menu = ModuleButton(mid=0, text='首页')
        menu.clicked_module.connect(self.module_menu_clicked)
        self.layout().addWidget(menu)

    # 设置菜单按钮
    def setMenus(self, menu_obj_list):
        self.clear()
        # print('添加前模块菜单个数%d个 %s' % (self.layout().count(), 'piece.base.ModuleBar.setMenus'))
        if len(menu_obj_list) > 1:
            system_menu = menu_obj_list.pop(0)
            menu_obj_list.append(system_menu)
        for menu_dict_item in menu_obj_list:
            menu = ModuleButton(mid=menu_dict_item['id'], text=menu_dict_item['name'])
            sub_module_items = menu_dict_item['subs']
            if sub_module_items:  # 有子菜单
                drop_down_menu = DropdownMenu()  # 创建下拉菜单
                drop_down_menu.triggered.connect(self.module_action_selected)  # 下拉菜单信号
                # 先加入原来的模块
                # drop_action = drop_down_menu.addAction(menu_dict_item['name'])
                # drop_action.aid = menu_dict_item['id']
                for sub_module in sub_module_items:
                    drop_action = drop_down_menu.addAction(sub_module['name'])
                    drop_action.aid = sub_module['id']
                    if sub_module['name'] == "数据管理":
                        sub_module_menu = DropdownMenu()
                        # sub_module_menu.triggered.connect(self.module_action_selected)
                        for sub_action in ["首页管理", "产品服务", '基本分析','交割服务']:
                            sub_action = sub_module_menu.addAction(sub_action)
                            sub_action.aid = -9
                        drop_action.setMenu(sub_module_menu)
                menu.setMenu(drop_down_menu)
            else:  # 没有子菜单关联原菜单的点击事件
                menu.clicked_module.connect(self.module_menu_clicked)
            self.layout().addWidget(menu)
        # print('添加后模块菜单个数%d个 %s' % (self.layout().count(), 'piece.base.ModuleBar.setMenus'))

    # 设置管理菜单
    def setMenuActions(self, actions):
        # print('设置管理菜单')
        if not actions:
            return
        self.actions_menu.clear()
        self.system_manager_button.setText('系统管理')
        for action_item in actions:
            action = self.actions_menu.addAction(action_item['name'])
            action.aid = action_item['id']
        self.system_manager_button.setMenu(self.actions_menu)
        self.layout().addWidget(self.system_manager_button)
        self.system_manager_button.show()

    # 菜单被点击了
    def module_menu_clicked(self, button):
        self.menu_clicked.emit(button.mid, button.text())

    # 管理菜单选择了
    def module_action_selected(self, action):
        # self.system_manager_button.setText(action.text())
        self.menu_clicked.emit(action.aid, action.text())


# 登录信息栏
class PermitBar(QWidget):
    to_usercenter = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(PermitBar, self).__init__(*args, **kwargs)
        self.user_id = None
        layout = QHBoxLayout(margin=0, spacing=0)
        # 用户头像
        self.avatar = CAvatar(self, shape=CAvatar.Circle, url='media/avatar.png', size=QSize(22, 22),
                              objectName='userAvatar')
        self.avatar.clicked.connect(self.to_user_center)
        layout.addWidget(self.avatar, alignment=Qt.AlignRight)
        # 用户名
        self.username_shown = QPushButton('用户名用户名', parent=self, objectName='usernameShown', clicked=self.to_user_center)
        layout.addWidget(self.username_shown, alignment=Qt.AlignRight)
        # 按钮
        self.login_button = QPushButton('登录', parent=self, objectName='loginBtn')
        layout.addWidget(self.login_button, alignment=Qt.AlignRight)
        self.register_button = QPushButton('注册', parent=self, objectName='registerBtn')
        layout.addWidget(self.register_button, alignment=Qt.AlignRight)
        self.logout_button = QPushButton('注销', parent=self, objectName='logoutBtn')
        layout.addWidget(self.logout_button, alignment=Qt.AlignRight)
        self.setLayout(layout)
        # 样式、属性
        self.username = ''
        self.timer_finished_count = 0
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.register_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.initial_show()  # 初始显示的控件
        self.setObjectName('permitBar')
        self.setStyleSheet("""
        #permitBar{
            min-height:22px;
            max-height:22px;
        }
        #loginBtn,#registerBtn,#logoutBtn{
            border:none;
            padding-left: 2px;
            padding-right: 4px;
            color: #FFFFFF;
        }
        #logoutBtn{
            margin-right:5px;
        }
        #loginBtn:hover,#registerBtn:hover,#logoutBtn:hover {
            color: rgb(54,220,180);

        }
        #usernameShown{
            margin-left: 3px;
            border:none;
            padding: 0 2px;
        }
        /*
        #userAvatar{
            background-color: rgb(100,255,120);
            min-width:22px;
            border-radius: 12px;
            margin-right: 2px;
        }
        */
        """)

    def initial_show(self):
        self.avatar.hide()
        self.username_shown.hide()
        self.logout_button.hide()

    # 设置用户id
    def set_user_id(self, uid):
        self.user_id = uid

    # 前往用户中心
    def to_user_center(self):
        if not self.user_id:
            return
        self.to_usercenter.emit(self.user_id)

    # 显示用户名
    def show_username(self, username):
        self.avatar.show()
        self.username_shown.setText(username + " ")  # 加空格防止初始动态化的时候跳动
        self.username = username
        self.username_shown.show()
        self.login_button.hide()
        self.register_button.hide()
        self.logout_button.show()
        if hasattr(self, 'timer'):
            self.timer.deleteLater()
            del self.timer
        self.timer = QTimer()
        self.timer.start(500)
        self.timer.timeout.connect(self._dynamic_username)

    # 设置头像
    def setAvatar(self, avatar_url):
        self.avatar.setUrl(avatar_url)

    # 用户注销
    def user_logout(self):
        self.username_shown.setText('')
        self.username = ''
        self.username_shown.hide()
        self.logout_button.hide()
        self.avatar.hide()
        self.login_button.show()
        self.register_button.show()
        if hasattr(self, 'timer'):
            # print('注销销毁定时器piece.base.PermitBar.user_logout()')
            self.timer.stop()
            self.timer.deleteLater()
            del self.timer

    # 设置用户名滚动显示
    def _dynamic_username(self):
        if self.timer_finished_count == len(self.username):
            self.username_shown.setText(self.username + " ")
            self.timer_finished_count = 0
        else:
            text = self.username[self.timer_finished_count:] + " " + self.username[:self.timer_finished_count]
            self.username_shown.setText(text)
            self.timer_finished_count += 1


# 导航栏
class NavigationBar(QWidget):
    clicked_login_button = pyqtSignal()
    clicked_register_button = pyqtSignal()
    clicked_logout_button = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(NavigationBar, self).__init__(*args, **kwargs)
        # 模块菜单栏
        self.module_bar = ModuleBar(parent=self, objectName='moduleBar')
        # 登录信息栏
        self.permit_bar = PermitBar(parent=self, objectName='permitBar')
        # 信号连接
        self.permit_bar.login_button.clicked.connect(self.clicked_login_button.emit)
        self.permit_bar.register_button.clicked.connect(self.clicked_register_button.emit)
        self.permit_bar.logout_button.clicked.connect(self.clicked_logout_button.emit)
        # 布局
        layout = QHBoxLayout(margin=0)
        layout.addWidget(self.module_bar, alignment=Qt.AlignLeft)
        layout.addWidget(self.permit_bar, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.setAttribute(Qt.WA_StyledBackground, True)  # 支持qss设置背景颜色(受父窗口透明影响qss会透明)
        self.setAutoFillBackground(True)  # 受父窗口影响(父窗口已设置透明)会透明,填充默认颜色
        self.setObjectName('navigationBar')
        self.setMouseTracking(True)
        self.setFixedHeight(settings.NAVIGATION_BAR_HEIGHT)
        self.setStyleSheet("""
        #navigationBar{
            background-color:rgb(34,102,185);
        }
        """)

    # 鼠标移动
    def mouseMoveEvent(self, event):
        # 接受事件不传递到父控件
        event.accept()


# 主窗口(无边框)
class FrameLessWindow(QWidget):
    # 枚举左上右下以及四个定点
    Left, Top, Right, Bottom, LeftTop, RightTop, LeftBottom, RightBottom = range(8)
    MARGIN = 5  # 边缘宽度小用于调整窗口大小

    def __init__(self, *args, **kwargs):
        super(FrameLessWindow, self).__init__(*args, **kwargs)
        # self.mousePressed = False
        # 设置窗体的图标和名称
        self.setWindowIcon(QIcon("media/logo.png"))
        self.setWindowTitle("瑞达期货研究院分析决策系统")
        # 标题栏
        self.title_bar = TitleBar(parent=self)
        # 导航栏
        self.navigation_bar = NavigationBar(parent=self)
        # 导航栏的信号
        self.navigation_bar.clicked_login_button.connect(self.user_to_login)
        self.navigation_bar.clicked_register_button.connect(self.user_to_register)
        self.navigation_bar.clicked_logout_button.connect(self.user_to_logout)
        self.navigation_bar.module_bar.menu_clicked.connect(self.module_clicked)  # 选择了某个模块的
        self.navigation_bar.permit_bar.to_usercenter.connect(self.skip_to_usercenter)  # 跳转至用户中心
        # 窗口承载体
        self.page_container = LoadedPage(parent=self)
        # 属性、样式
        user_desktop = QDesktopWidget().availableGeometry()  # 用户的桌面信息,来改变自身窗体大小
        max_width = user_desktop.width()
        max_height = user_desktop.height()
        self.resize(max_width * 0.7, max_width * 0.8 * 0.518)
        self.setMaximumSize(max_width, max_height)  # 最大为用户桌面大小
        self.setMinimumSize(max_width * 0.5, max_height * 0.5)  # 最小为用户桌面大小的一半
        my_frame = self.frameGeometry()  # 1 (三步法放置桌面中心)自身窗体信息(虚拟框架)
        my_frame.moveCenter(user_desktop.center())  # 2 框架中心移动到用户桌面中心
        self.move(my_frame.topLeft())  # 3 窗口左上角与虚拟框架左上角对齐
        self.setWindowFlags(Qt.FramelessWindowHint)  # 无边框
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 背景全透明(影响子窗口)
        self._pressed = False
        self._direction = None
        self._mouse_pos = None
        self.setMouseTracking(True)  # 鼠标不点下移动依然有效(针对本窗口, 子控件无效)
        self.title_bar.installEventFilter(self)  # 子控件安装事件事件过滤
        self.navigation_bar.installEventFilter(self)
        self.page_container.installEventFilter(self)
        # 布局
        layout = QVBoxLayout(margin=self.MARGIN, spacing=0)
        layout.addWidget(self.title_bar)
        layout.addWidget(self.navigation_bar)
        layout.addWidget(self.page_container)
        self.setLayout(layout)

    def close(self):
        super(FrameLessWindow, self).close()
        # 清理缓存目录
        cache_path = os.path.join(settings.BASE_DIR, 'cache/')
        shutil.rmtree(cache_path)
        os.mkdir(cache_path)

    def show(self):
        super(FrameLessWindow, self).show()
        # 创建缓存目录
        cache_path = os.path.join(settings.BASE_DIR, 'cache/')
        if not os.path.exists(cache_path):
            os.mkdir(cache_path)

    # 事件过滤器, 用于解决鼠标进入其它控件后还原为标准鼠标样式
    def eventFilter(self, obj, event):
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
            self._direction = None  # 去除方向
            self._pressed = None  # 去除按下标记
        return super(FrameLessWindow, self).eventFilter(obj, event)

    # 鼠标按下事件
    def mousePressEvent(self, event):
        super(FrameLessWindow, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.pos()
            self._pressed = True

    # 鼠标弹起事件
    def mouseReleaseEvent(self, event):
        super(FrameLessWindow, self).mouseReleaseEvent(event)
        self._pressed = False
        self._direction = None

    # 鼠标移动事件(只有边框MARGIN大小范围有效果,因为其他的是其子控件)(会捕获子控件的鼠标按住移动的事件)
    def mouseMoveEvent(self, event):
        super(FrameLessWindow, self).mouseMoveEvent(event)
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

    # 由于是全透明背景窗口,重绘事件中绘制透明度为1的难以发现的边框,用于调整窗口大小
    def paintEvent(self, event):
        super(FrameLessWindow, self).paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(155, 255, 255, 1), 2 * self.MARGIN))
        painter.drawRect(self.rect())

    # 调整窗口大小
    def resize_window(self, pos):
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

    # 窗口最大化去除边界MARGIN
    def showMaximized(self):
        super(FrameLessWindow, self).showMaximized()
        self.layout().setContentsMargins(0, 0, 0, 0)

    # 还原保留调整大小的边界
    def showNormal(self):
        super(FrameLessWindow, self).showNormal()
        self.layout().setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
