# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-27
# ------------------------
import json
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,QGridLayout, QFrame, QTableWidget, \
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QDialog, QTextEdit, QScrollBar
from PyQt5.QtCore import QMargins, QUrl, Qt, pyqtSignal, QPoint, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QCursor, QBrush, QColor, QFont
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from channels.delivery import WarehouseMapChannel
from widgets import CAvatar, Paginator, PDFContentPopup
from utils.client import get_user_token
from settings import SERVER_API, SERVER_ADDR, STATIC_PREFIX, USER_AGENT, STATIC_URL


class MenuPushButton(QPushButton):
    to_show_child_widget = pyqtSignal(int, int, int)
    to_hide_child_widget = pyqtSignal()

    def __init__(self, button_id, *args, **kwargs):
        super(MenuPushButton, self).__init__(*args)
        self.setMouseTracking(True)
        self.id = button_id
        self.children_menus = None

        self.setObjectName('menuPushButton')
        self.setStyleSheet("""
        #menuPushButton{
            border: 1px solid #fff;
            padding: 2px 5px;
        }   
        """)

    def enterEvent(self, event):
        self.to_show_child_widget.emit(self.id, self.pos().x(), self.pos().y())

    def leaveEvent(self, event):
        self.to_hide_child_widget.emit()

    def set_children_menu(self, children):
        self.children_menus = children

    def get_children_menu(self):
        return self.children_menus


class ChildrenMenuWidget(QWidget):
    """ 菜单的子菜单控件 """
    def __init__(self, *args, **kwargs):
        super(ChildrenMenuWidget, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.95)
        self.setObjectName('childrenMenu')
        self.setStyleSheet("""
        #childrenMenu{
            background-color:rgb(200,200,200);
        }
        """)

    def weather_to_hide(self):
        """ 按条件关闭/隐藏的槽函数"""
        # 鼠标离开了父菜单，要判断鼠标的位置，如果不在控件内就隐藏
        cursor_pos_x, cursor_pos_y = QCursor.pos().x(), QCursor.pos().y()
        my_pos_x, my_pos_y = self.pos().x(), self.pos().y() - 2  # 减2像素确保离开父菜单进入子菜单的过渡，这个值由父菜单按钮的border和子菜单控件的y偏移量决定
        my_width, my_height = self.width(), self.height()
        if my_pos_x <= cursor_pos_x <= my_pos_x + my_width and my_pos_y <= cursor_pos_y <= my_pos_y + my_height:
            pass
        else:
            self.close()

    def leaveEvent(self, event):
        self.close()

    def close(self):
        super(ChildrenMenuWidget, self).close()
        self.clear_layout()

    def clear_layout(self):
        my_layout = self.layout()
        if my_layout is not None:
            for index in range(self.layout().count()):
                widget = self.layout().itemAt(index).widget()
                if widget is not None:
                    widget.deleteLater()
                    del widget
            my_layout.deleteLater()
            del my_layout


class MenuBar(QWidget):
    """菜单栏"""

    def __init__(self, *args, **kwargs):
        super(MenuBar, self).__init__(*args, **kwargs)
        self.setFixedHeight(22)
        self.parent = None  # 自己设置引用，不然QScrollArea一包裹找不到parent
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(8, 0, 0, 0))
        layout.addStretch()

        # self.user_bar = UserBar(self)
        # layout.addWidget(self.user_bar, alignment=Qt.AlignRight)

        self.setLayout(layout)

        self.setObjectName('menuBar')
        # self.setStyleSheet("""
        # #menuBar{
        #     background-color: rgb(34,102,175);
        # }
        # """)

        # 子菜单控件
        self.child_menus_widget = ChildrenMenuWidget(self)
        self.child_menus_offset_x = 0
        self.child_menus_offset_y = 0

    def set_parent(self, parent):
        self.parent = parent

    def mouseMoveEvent(self, event):
        super(MenuBar, self).mouseMoveEvent(event)
        event.accept()

    def clear_menus(self):
        for index in range(self.layout().count()):
            menu_widget = self.layout().itemAt(index).widget()
            if menu_widget is not None:
                menu_widget.deleteLater()
                del menu_widget

    def set_menus(self, menus_list):
        self.clear_menus()
        for index, menu_item in enumerate(menus_list):
            menu = MenuPushButton(menu_item['id'], menu_item['text'])
            menu.set_children_menu(menu_item['children'])
            menu.to_show_child_widget.connect(self.show_child_menus)  # 显示子菜单的信号
            menu.to_hide_child_widget.connect(self.weather_to_hide_children_menu)  # 关闭子菜单的信号
            self.layout().insertWidget(index, menu)

    def get_menu(self, menu_id):
        """获取指定id的菜单按钮实例"""
        menu_widget = None
        for index in range(self.layout().count()):
            menu_widget = self.layout().itemAt(index).widget()
            if menu_widget is not None:
                if menu_widget.id == menu_id:
                    menu_widget = menu_widget
                    break
        return menu_widget

    def show_child_menus(self, parent_menu_id, offset_x, offset_y):
        """显示子菜单控件"""
        self.child_menus_widget.deleteLater()
        del self.child_menus_widget
        self.child_menus_widget = ChildrenMenuWidget(self)
        parent_menu = self.get_menu(parent_menu_id)
        layout = self.parent.set_children_menu_layout(parent_menu_id, parent_menu.get_children_menu())
        self.child_menus_widget.setLayout(layout)
        self.child_menus_offset_x = offset_x
        self.child_menus_offset_y = offset_y + 20  # 18为菜单按钮的固定高度
        self.child_menus_widget.move(self.mapToGlobal(QPoint(0, 0)).x() + self.child_menus_offset_x, self.mapToGlobal(QPoint(0, 0)).y() + self.child_menus_offset_y)
        self.child_menus_widget.show()

    def weather_to_hide_children_menu(self):
        self.child_menus_widget.weather_to_hide()


# 品种菜单按钮
class VarietyButton(QPushButton):
    select_variety_menu = pyqtSignal(int, str)

    def __init__(self, bid, v_en, text, *args):
        super(VarietyButton, self).__init__(*args)
        self.bid = bid
        self.v_en = v_en
        self.setText(text)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.mouse_clicked)
        self.setObjectName("button")
        self.setStyleSheet("""
        #button{
            border:1px solid rgb(34,142,125);
            padding: 2px 0;
            margin-top:2px;
            margin-bottom:2px;
            font-size: 13px;
            min-width: 65px;
            max-width: 65px;
            border-radius:3px;
        }
        #button:hover{
            color:rgb(200,120,200);
            background-color:rgb(225,225,225);
            border-radius:3px;
        }
        #button:pressed{
            background-color:rgb(150,150,180);
            color:rgb(250,250,250);
            border-radius:3px;
        }
        """)

    def mouse_clicked(self):
        self.select_variety_menu.emit(self.bid, self.v_en)


# 地区按钮菜单
class AreaButton(QPushButton):
    select_area_menu = pyqtSignal(str)

    def __init__(self, *args):
        super(AreaButton, self).__init__(*args)
        self.clicked.connect(self.mouse_clicked)
        self.setObjectName("button")
        self.setStyleSheet("""
        #button{
            border:1px solid rgb(34,142,125);
            padding: 2px 0;
            margin-top:2px;
            margin-bottom:2px;
            font-size: 13px;
            min-width: 65px;
            max-width: 65px;
            border-radius:3px;
        }
        #button:hover{
            color:rgb(200,120,200);
            background-color:rgb(225,225,225);
            border-radius:3px;
        }
        #button:pressed{
            background-color:rgb(150,150,180);
            color:rgb(250,250,250);
            border-radius:3px;
        }
        """)

    def mouse_clicked(self):
        self.select_area_menu.emit(self.text())


# 自定义菜单按钮
class CustomMenuButton(QPushButton):
    def __init__(self, text, width, *args):
        super(CustomMenuButton, self).__init__(*args)
        self.setText(text)
        self.setFixedWidth(width)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("button")
        self.setStyleSheet("""
        #button{
            border:1px solid rgb(34,142,125);
            padding: 2px 0;
            margin-top:2px;
            margin-bottom:2px;
            font-size: 13px;
            border-radius:3px;
        }
        #button:hover{
            color:rgb(200,120,200);
            background-color:rgb(225,225,225);
            border-radius:3px;
        }
        #button:pressed{
            background-color:rgb(150,150,180);
            color:rgb(250,250,250);
            border-radius:3px;
        }
        """)


""" 交流与讨论相关 """


# 回复的项目
class ReplyItem(QWidget):
    def __init__(self, reply_item, *args, **kwargs):
        super(ReplyItem, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        reply_layout = QVBoxLayout(self)
        user_layout = QHBoxLayout(self)
        avatar_url = STATIC_PREFIX + reply_item['avatar'] if reply_item['avatar'] else "media/default_avatar.png"
        avatar = CAvatar(url=avatar_url,size=QSize(20, 20), parent=self)
        user_layout.addWidget(avatar)
        user_layout.addWidget(QLabel(reply_item['username'], self))
        user_layout.addStretch()
        user_layout.addWidget(QLabel(reply_item['create_time'], self))
        reply_layout.addLayout(user_layout)
        text_label = QLabel(self)
        text_label.setText(reply_item['text'])
        reply_layout.addWidget(text_label)
        self.setLayout(reply_layout)


# 讨论的项目
class DiscussItem(QWidget):
    reply_discussion = pyqtSignal(int)

    def __init__(self, discuss,*args, **kwargs):
        super(DiscussItem, self).__init__(*args, **kwargs)
        self.replies = discuss['replies']
        self.is_show_replies = False  # 标记是否已经展开了回复
        self.dis_id = discuss['id']
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,0,0,0))
        layout.setSpacing(1)
        discuss_title = QWidget(self)
        discuss_title.setFixedHeight(22)
        username_layout = QHBoxLayout(self)
        username_layout.setContentsMargins(QMargins(2,1,1,1))
        avatar_url = STATIC_PREFIX + discuss['avatar'] if discuss['avatar'] else "media/default_avatar.png"
        self.avatar = CAvatar(url=avatar_url,size=QSize(20,20), parent=self)
        username_layout.addWidget(self.avatar)
        self.username = QLabel(discuss['username'])
        username_layout.addWidget(self.username)
        username_layout.addStretch()
        self.dis_time = QLabel(discuss['create_time'])
        username_layout.addWidget(self.dis_time)
        discuss_title.setLayout(username_layout)
        layout.addWidget(discuss_title)

        self.text_show = QLabel(self)
        self.text_show.setWordWrap(True)  # 自动换行
        self.text_show.setText(self.get_style_text(discuss['text']))
        layout.addWidget(self.text_show)

        reply_layout = QHBoxLayout(self)
        reply_layout.addStretch()
        self.discuss_button = QPushButton('我来答', self)
        self.discuss_button.setCursor(Qt.PointingHandCursor)
        self.discuss_button.clicked.connect(self.user_reply_discussion)
        reply_layout.addWidget(self.discuss_button)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        reply_layout.addWidget(line)
        self.reply_button = QPushButton('讨论(' + str(len(self.replies)) + ')', self)
        self.reply_button.setCursor(Qt.PointingHandCursor)
        self.reply_button.clicked.connect(self.show_replies)
        reply_layout.addWidget(self.reply_button)

        layout.addLayout(reply_layout)
        self.setLayout(layout)

        self.discuss_button.setObjectName('discussBtn')
        self.reply_button.setObjectName('replyBtn')
        self.text_show.setObjectName('textLable')
        discuss_title.setObjectName('disTitle')

    def get_style_text(self, text):
        # 设置文字显示风格
        return "<div style='font-size:13px;text-indent:26px;line-height:20px'>" + text + "</div>"

    def show_replies(self):
        if self.is_show_replies:  # 已经展开的要关闭
            self.close_replies()
            return
        for reply_item in self.replies:
            reply_item['text'] = self.get_style_text(reply_item['text'])
            reply_widget = ReplyItem(reply_item)
            self.layout().insertWidget(self.layout().count(), reply_widget)
        self.is_show_replies = True

    def reset_replies(self):
        self.close_replies()
        self.show_replies()

    def user_reply_discussion(self):
        self.reply_discussion.emit(self.dis_id)

    # 关闭回复
    def close_replies(self):
        for index in range(self.layout().count()):
            widget = self.layout().itemAt(index).widget()
            if isinstance(widget, ReplyItem):
                widget.close()
                widget.deleteLater()
                del widget
        self.is_show_replies = False

    def set_replies(self, replies, reply_id):
        if reply_id == self.dis_id:
            self.replies = replies
            self.reply_button.setText('讨论(' + str(len(self.replies)) + ')')
            if self.is_show_replies:
                self.reset_replies()
            return True
        else:
            return False


# 最新交流与讨论的控件
class DiscussWidget(QScrollArea):
    reply_discussion = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(DiscussWidget, self).__init__(*args, **kwargs)
        self.dis_container = QWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,0,0,5))
        # 具体交流与讨论的项目
        self.dis_container.setLayout(layout)
        self.setWidget(self.dis_container)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addStretch()
        self.dis_container.setLayout(layout)
        self.setObjectName("disScroll")
        self.setStyleSheet("""
        #disScroll{border:none}
        """)

    def add_discuss_item(self, item):
        item.setParent(self)
        item.setStyleSheet("""
        #disTitle{background-color:rgb(150,200,210)}
        #textLable{background-color:rgb(240,240,240);}
        #discussBtn,#replyBtn{border:none;color:rgb(100,150,200)}
        """)
        item.reply_discussion.connect(self.reply_discussion)
        self.dis_container.layout().insertWidget(self.dis_container.layout().count() - 1, item)

    def set_replies(self, replies, reply_id):
        for index in range(self.dis_container.layout().count()):
            widget = self.dis_container.layout().itemAt(index).widget()
            if isinstance(widget, DiscussItem):
                if widget.set_replies(replies, reply_id):
                    break


# 更多讨论交流页面的讨论控件
class MoreDiscussPageWidget(QWidget):
    reply_discussion = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(MoreDiscussPageWidget, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,0,0,0))
        # 具体交流与讨论的项目
        layout.addStretch()
        self.setLayout(layout)
        self.setObjectName("disScroll")
        self.setStyleSheet("""
        #disScroll{border:none}
        """)

    def add_discuss_item(self, item):
        item.setParent(self)
        item.setStyleSheet("""
        #disTitle{background-color:rgb(200,230,230)}
        #textLable{background-color:rgb(240,240,240);}
        #discussBtn,#replyBtn{border:none;color:rgb(100,150,200)}
        """)
        item.reply_discussion.connect(self.reply_discussion)
        self.layout().insertWidget(self.layout().count() - 1, item)

    def clear_discuss_items(self):
        for index in range(self.layout().count()):
            widget = self.layout().itemAt(index).widget()
            if isinstance(widget, DiscussItem):
                widget.deleteLater()
                del widget

    def set_replies(self, replies, reply_id):
        for index in range(self.layout().count()):
            widget = self.layout().itemAt(index).widget()
            if isinstance(widget, DiscussItem):
                if widget.set_replies(replies, reply_id):
                    break


# 显示仓库的表格
class WarehouseTable(QTableWidget):
    def __init__(self, *args):
        super(WarehouseTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setMouseTracking(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QHeaderView.SelectRows)
        self.setEditTriggers(QHeaderView.NoEditTriggers)
        self.verticalHeader().hide()
        self.horizontalHeader().setStyleSheet("""
        QHeaderView::section,
        QTableCornerButton::section {
            min-height: 25px;
            padding: 1px;border: none;
            border-right: 1px solid rgb(201,202,202);
            border-bottom: 1px solid rgb(201,202,202);
            background-color:rgb(150,200,210);
            font-weight: bold;
            font-size: 13px;
            min-width:26px;
        }""")

        self.setStyleSheet("""
        QTableWidget{
            font-size: 13px;
            alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
        }
        QTableWidget::item{
            border-bottom: 1px solid rgb(201,202,202);
            border-right: 1px solid rgb(201,202,202);
        }
        QTableWidget::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 4:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # 以地区获取仓库信息的显示方式
    def area_warehouse_show(self, warehouses):
        table_headers = ["地区", "交割仓库", "地址", "交割品种", "查看"]
        self.clear()
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(warehouses))
        self.setHorizontalHeaderLabels(table_headers)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(warehouses):
            self.setRowHeight(row, 30)
            item0 = QTableWidgetItem(row_item['area'])
            item0.id = row_item['id']
            item0.fixed_code = row_item["fixed_code"]
            item0.variety_en = None
            item0.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['name'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['addr'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['delivery_varieties'])
            item3.setToolTip(row_item['delivery_varieties'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem('详情')
            item4.setTextAlignment(Qt.AlignCenter)
            item4.setForeground(QBrush(QColor(100, 150,200)))
            self.setItem(row, 4, item4)
        self.setFixedHeight(self.rowCount() * 30 + 35)

    # 以品种获取仓库的显示方式
    def variety_warehouse_show(self, warehouses):
        self.clear()
        table_headers = ["品种", "交割仓库", "地址", "联系人", "联系方式", "升贴水", "查看"]
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(warehouses))
        self.setHorizontalHeaderLabels(table_headers)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(warehouses):
            self.setRowHeight(row,30)
            item0 = QTableWidgetItem(row_item['variety'])
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.fixed_code = row_item['fixed_code']
            item0.variety_en = row_item['variety_en']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['name'])
            item1.setToolTip(row_item['name'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['addr'])
            item2.setToolTip(row_item['addr'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['linkman'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['links'])
            item4.setToolTip(row_item['links'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['premium'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)
            item6 = QTableWidgetItem('仓单')
            item6.setForeground(QBrush(QColor(100, 150, 200)))
            item6.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 6, item6)
        self.setFixedHeight(self.rowCount() * 30 + 35)


# 显示详细仓单的控件
class DetailWarehouseReceipts(QScrollArea):
    closed_signal = pyqtSignal()

    def __init__(self, warehouses_receipts, *args, **kwargs):
        super(DetailWarehouseReceipts, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.container = QWidget(self)
        layout = QVBoxLayout(self)
        info_layout = QHBoxLayout(self)
        info_layout.addStretch()
        info_layout.addWidget(QLabel('仓库名称:', self, objectName='titleLabel'), alignment=Qt.AlignLeft)
        info_layout.addWidget(QLabel(warehouses_receipts['warehouse'], self, objectName='warehouseName', textInteractionFlags=Qt.TextSelectableByMouse))
        info_layout.addStretch()
        font = QFont()
        font.setFamily('webdings')
        self.close_button = QPushButton('r', self)
        self.close_button.setFont(font)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setObjectName('closeButton')
        self.close_button.clicked.connect(self.close_widget)
        info_layout.addWidget(self.close_button)
        layout.addLayout(info_layout)

        layout.addWidget(QLabel(warehouses_receipts['short_name'], self, textInteractionFlags=Qt.TextSelectableByMouse), alignment=Qt.AlignCenter)

        info_layout = QHBoxLayout(self)
        info_layout.addWidget(QLabel('<div>仓&nbsp;库&nbsp;地&nbsp;址:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
        info_layout.addWidget(QLabel(warehouses_receipts['addr'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
        info_layout.addStretch()
        layout.addLayout(info_layout)

        for variety_item in warehouses_receipts['varieties']:
            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>交&nbsp;割&nbsp;品&nbsp;种:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['name'], self, objectName='infovarietyMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>联&nbsp;&nbsp;系&nbsp;&nbsp;人:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['linkman'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>联&nbsp;系&nbsp;方&nbsp;式:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['links'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>升&nbsp;&nbsp;贴&nbsp;&nbsp;水:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['premium'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>仓&nbsp;单&nbsp;有效期:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            l = QLabel(variety_item['receipt_expire'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse)
            l.setMinimumWidth(500)
            l.setWordWrap(True)
            info_layout.addWidget(l)
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>最&nbsp;后&nbsp;交易日:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            label = QLabel(variety_item['last_trade'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse)
            label.setMinimumWidth(500)
            label.setWordWrap(True)
            info_layout.addWidget(label)
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>交&nbsp;割&nbsp;单&nbsp;位:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['delivery_unit'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>仓&nbsp;单&nbsp;单&nbsp;位:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['receipt_unit'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>交割月投机限仓:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft | Qt.AlignTop)
            info_layout.addWidget(QLabel(variety_item['limit_holding'], self, objectName='infoMsg', textInteractionFlags=Qt.TextSelectableByMouse))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            layout.addWidget(QLabel('【仓单信息】', self, objectName='receiptLabel'))
            receipt_table = QTableWidget(self)
            receipt_table.setObjectName('receiptTable')
            receipt_table.verticalHeader().hide()
            receipt_table.setFrameShape(QFrame.NoFrame)
            receipt_table.setAlternatingRowColors(True)
            receipt_table.setShowGrid(False)
            receipt_table.setFocusPolicy(Qt.NoFocus)
            receipt_table.setEditTriggers(QHeaderView.NoEditTriggers)
            receipt_table.setSelectionBehavior(QHeaderView.SelectRows)
            receipt_table.setColumnCount(3)
            receipt_table.setHorizontalHeaderLabels(['日期', '仓单', '增减'])
            receipt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            receipt_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            receipt_table.horizontalHeader().setStyleSheet("QHeaderView::section,"
                                                           "QTableCornerButton::section {"
                                                           "min-height: 25px;"
                                                           "padding: 1px;"
                                                           "border: none;"
                                                           "border-right: 1px solid rgb(201,202,202);"
                                                           "border-bottom: 1px solid rgb(201,202,202);"
                                                           "background-color:rgb(150,200,210);"
                                                           "font-weight: bold;"
                                                           "font-size: 13px;"
                                                           "min-width:26px;}"
                                                           )
            for row, receipt_item in enumerate(variety_item['receipts']):
                receipt_table.insertRow(row)
                receipt_table.setRowHeight(row, 30)
                date = receipt_item['date']
                date = date[:4] + '-' + date[4:6] + '-' + date[6:]
                item0 = QTableWidgetItem(date)
                item0.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 0, item0)
                item1 = QTableWidgetItem(str(receipt_item['receipt']))
                item1.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 1, item1)
                item2 = QTableWidgetItem(str(receipt_item['increase']))
                item2.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 2, item2)

            receipt_table.setFixedHeight(receipt_table.rowCount() * 30 + 28)
            layout.addWidget(receipt_table)

        layout.addStretch()

        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

        # 详情信息显示动画
        self.detail_animation = QPropertyAnimation(self, b'geometry')
        self.detail_animation.setParent(self)
        self.detail_animation.setDuration(300)

        self.setObjectName('detailReceipt')
        self.container.setStyleSheet("""
        #detailReceipt{background-color:rgb(240,240,240)}
        #titleLabel{font-size:13px;font-weight:bold;}
        #closeButton{border:none;color:rgb(200,100,100)}
        #warehouseName{font-size:14px;color:rgb(100,150,220);font-weight:bold}
        #infoLabel{font-size:13px;font-weight:bold}
        #receiptLabel{font-size:14px;color:rgb(100,200,220)}
        #infoMsg,#infovarietyMsg{font-size:14px}
        #infovarietyMsg{color:rgb(200,80,80);font-weight:bold}
        #receiptTable{font-size: 13px;alternate-background-color: rgb(245, 250, 248);}
        #receiptTable::item{border-bottom: 1px solid rgb(201,202,202);border-right: 1px solid rgb(201,202,202);}
        #receiptTable::item:selected{background-color: rgb(215, 215, 215);}
        """)
        self.verticalScrollBar().setStyleSheet("""
        QScrollBar:vertical {
            background: transparent; 
            width: 8px; 
            margin: 0px 0px 0px 0px; 
            padding-top: 12px; 
            padding-bottom: 12px;
        }
        QScrollBar:vertical:hover{
            background: rgba(0, 0, 0, 30);
            border-radius: 8px; 
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 50);
            width: 8px;
            border-radius: 8px;
            border: none;
        }
        QScrollBar::handle:vertical:hover{background: rgba(0, 0, 0, 100);}
        QScrollBar::add-page:vertical {
            width: 10px;
            background: transparent;
        }
        QScrollBar::sub-page:vertical {
            width: 10px;
            background: transparent;
        }
        QScrollBar::sub-line:vertical {
            height: 12px;
            width: 5px;
            background: transparent;
            subcontrol-position: top;
        }
        QScrollBar::up-arrow:vertical {
            image: url(media/scrollbar/scrollbar_arrowup_normal.png);
        }
        QScrollBar::up-arrow:vertical:hover {
            image: url(media/scrollbar/scrollbar_arrowup_down.png);
        }
        QScrollBar::up-arrow:vertical:pressed {
            image: url(media/scrollbar/scrollbar_arrowup_highlight.png);
        }
        QScrollBar::add-line:vertical {
            height: 12px;
            width: 5px;
            background: transparent;
            subcontrol-position: bottom;
        }
        QScrollBar::down-arrow:vertical {
            image: url(media/scrollbar/scrollbar_arrowdown_normal.png);
        }
        QScrollBar::down-arrow:vertical:hover {
            image: url(media/scrollbar/scrollbar_arrowdown_down.png);
        }
        QScrollBar::down-arrow:vertical:pressed {
            image: url(media/scrollbar/scrollbar_arrowdown_highlight.png);
        }
        """)

    def close_widget(self):
        self.closed_signal.emit()


# 重写事件，防止滚动地图大小时整个页面滚动
class WebEngineView(QWebEngineView):
    def wheelEvent(self, event):
        super(WebEngineView, self).wheelEvent(event)
        event.accept()


# 更多讨论交流
class MoreDiscussWidget(QWidget):
    reply_discussion = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(MoreDiscussWidget, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        opts_layout = QHBoxLayout(self)
        self.search_edit = QLineEdit(self)
        self.search_button = QPushButton('搜索', self)
        self.search_button.clicked.connect(self.query_keyword_discussion)

        opts_layout.addWidget(self.search_edit)
        opts_layout.addWidget(self.search_button)
        # 页码控制器
        self.paginator = Paginator(parent=self)
        self.paginator.clicked.connect(self._get_discuss_message)
        opts_layout.addWidget(self.paginator)
        opts_layout.addStretch()
        self.myself_button = QPushButton('我的问题', self)
        self.myself_button.clicked.connect(self.query_own_discussion)
        self.question_button = QPushButton('我要提问', self)
        self.question_button.clicked.connect(self.new_question)
        opts_layout.addWidget(self.myself_button)
        opts_layout.addWidget(self.question_button)
        layout.addLayout(opts_layout)
        # 显示具体条目的widget
        self.discuss_widget = MoreDiscussPageWidget(self)
        self.discuss_widget.reply_discussion.connect(self.reply_discussion)
        layout.addWidget(self.discuss_widget)
        self.setLayout(layout)

        self._get_discuss_message()

    def set_replies(self, replies, reply_id):
        self.discuss_widget.set_replies(replies, reply_id)

    def query_own_discussion(self):
        """ 查询用户自己提问的问题 """
        self._get_discuss_message(is_own=True, keyword=None)

    def query_keyword_discussion(self):
        """ 关键字查询 """
        self._get_discuss_message(keyword=self.search_edit.text())

    def _get_discuss_message(self, is_own=False, keyword=None):
        current_page = self.paginator.current_page
        if is_own:  # 查询自己发表的问题
            url = SERVER_API + 'delivery/discussion-own/'
        else:  # 分页查询所有问题
            url = SERVER_API + 'delivery/discussion/?c_page=' + str(current_page)
        if keyword is not None:  # 关键字查询问题
            url = SERVER_API + 'delivery/discussion-query/?keyword={}'.format(keyword)
        # 获取第一页交流与讨论的内容
        try:
            r = requests.get(url, headers={"Authorization": get_user_token()})
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError('获取讨论数据失败')
        except Exception:
            discuss = []
            total_page = 1
        else:
            discuss = response['discussions']
            total_page = response['total_page']
        # 清除当前所有讨论数据
        self.discuss_widget.clear_discuss_items()

        self.paginator.setTotalPages(total_page)
        for item_json in discuss:
            item = DiscussItem(item_json)
            self.discuss_widget.add_discuss_item(item)

    def new_question(self):
        # 提交新的问题

        def commit_question():
            content = popup.text_edit.toPlainText().strip()
            try:
                r = requests.post(
                    url=SERVER_API + 'delivery/discussion/',
                    headers={
                        'Content-Type': 'application/json;charset=utf8', 'User-Agent': USER_AGENT,
                        'Authorization': get_user_token()
                    },
                    data=json.dumps({"content": content})
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 201:
                    raise ValueError(response['detail'])
            except Exception as e:
                QMessageBox.information(popup, '错误', str(e))
            else:
                QMessageBox.information(popup, '成功', response['message'])
                popup.close()
                self._get_discuss_message()

        popup = QDialog(self)
        popup.resize(350,180)
        popup.setWindowTitle('新的讨论')
        popup.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(popup)
        popup.text_edit = QTextEdit(popup)
        layout.addWidget(popup.text_edit)
        popup.commit_button = QPushButton('提交', popup)
        popup.commit_button.clicked.connect(commit_question)
        layout.addWidget(popup.commit_button, alignment=Qt.AlignRight)
        popup.setLayout(layout)
        popup.exec_()


class DeliveryPage(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(DeliveryPage, self).__init__(*args, *kwargs)
        self.setAttribute(Qt.WA_StyleSheet, True)
        self.container = QWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        layout.setSpacing(1)
        map_discuss_layout = QHBoxLayout(self)
        map_discuss_layout.setContentsMargins(QMargins(0,0,4,0))
        map_discuss_layout.setSpacing(5)
        self.menu_bar = MenuBar(self)
        self.menu_bar.set_parent(self)
        layout.addWidget(self.menu_bar, alignment=Qt.AlignTop)

        self.map_view = WebEngineView(self)
        self.map_view.loadFinished.connect(self.resize_widgets)  # 加载结束调整地图和控件的大小
        self.map_view.load(QUrl("file:///pages/delivery/map.html"))

        channel_qt_obj = QWebChannel(self.map_view.page())  # 实例化qt信道对象,必须传入页面参数
        self.contact_channel = WarehouseMapChannel()  # 页面信息交互通道
        self.contact_channel.request_province_warehouses.connect(self.get_province_warehouses)
        self.contact_channel.request_warehouse_detail.connect(self.get_warehouse_receipts)
        self.map_view.page().setWebChannel(channel_qt_obj)
        channel_qt_obj.registerObject("pageContactChannel", self.contact_channel)  # 信道对象注册信道，只能注册一个

        map_discuss_layout.addWidget(self.map_view, alignment=Qt.AlignTop)

        # 讨论与交流
        dis_layout = QVBoxLayout(self)
        dis_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        dis_layout.setSpacing(5)
        dis_title_layout = QHBoxLayout(self)
        dis_title_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.dis_label = QLabel('【最新讨论】', self)
        dis_title_layout.addWidget(self.dis_label, alignment=Qt.AlignLeft)
        self.more_dis_button = QPushButton('更多>>', self)
        self.more_dis_button.setCursor(Qt.PointingHandCursor)
        self.more_dis_button.clicked.connect(self.more_discussion_widget)
        dis_title_layout.addWidget(self.more_dis_button, alignment=Qt.AlignRight)
        dis_layout.addLayout(dis_title_layout)

        self.discuss_show = DiscussWidget(self)
        self.discuss_show.reply_discussion.connect(self.user_reply_discussion)
        dis_layout.addWidget(self.discuss_show)

        map_discuss_layout.addLayout(dis_layout)

        layout.addLayout(map_discuss_layout)

        self.warehouse_table = WarehouseTable(self)
        self.warehouse_table.cellClicked.connect(self.warehouse_table_cell_clicked)
        self.warehouse_table.cellDoubleClicked.connect(self.warehouse_table_double_clicked)
        layout.addWidget(self.warehouse_table)

        # self.no_data_label = QLabel('没有数据', self)
        # layout.addWidget(self.no_data_label)
        # 显示仓库详情的控件
        self.detail_warehouse = None
        layout.addStretch()
        # 显示更多讨论交流页面的控件
        self.more_dis_widget = None

        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.more_dis_button.setObjectName('moreDisBtn')
        self.container.setStyleSheet("""
        #vscrollBar{width:5px;background-color:rgb(100,200,210)}
        #detailReceipt{border-top:rgb(200,210,230);background-color:rgb(100,120,80)}
        #moreDisBtn{border:none;color:rgb(100,120,200);}
        """)

        # 设置滚动条样式
        self.verticalScrollBar().setStyleSheet("""
        QScrollBar:vertical {
            background: transparent; 
            width: 8px; 
            margin: 0px 0px 0px 0px; 
            padding-top: 12px; 
            padding-bottom: 12px;
        }
        QScrollBar:vertical:hover{
            background: rgba(0, 0, 0, 30);
            border-radius: 8px; 
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 50);
            width: 8px;
            border-radius: 8px;
            border: none;
        }
        QScrollBar::handle:vertical:hover{background: rgba(0, 0, 0, 100);}
        QScrollBar::add-page:vertical {
            width: 10px;
            background: transparent;
        }
        QScrollBar::sub-page:vertical {
            width: 10px;
            background: transparent;
        }
        QScrollBar::sub-line:vertical {
            height: 12px;
            width: 5px;
            background: transparent;
            subcontrol-position: top;
        }
        QScrollBar::up-arrow:vertical {
            image: url(media/scrollbar/scrollbar_arrowup_normal.png);
        }
        QScrollBar::up-arrow:vertical:hover {
            image: url(media/scrollbar/scrollbar_arrowup_down.png);
        }
        QScrollBar::up-arrow:vertical:pressed {
            image: url(media/scrollbar/scrollbar_arrowup_highlight.png);
        }
        QScrollBar::add-line:vertical {
            height: 12px;
            width: 5px;
            background: transparent;
            subcontrol-position: bottom;
        }
        QScrollBar::down-arrow:vertical {
            image: url(media/scrollbar/scrollbar_arrowdown_normal.png);
        }
        QScrollBar::down-arrow:vertical:hover {
            image: url(media/scrollbar/scrollbar_arrowdown_down.png);
        }
        QScrollBar::down-arrow:vertical:pressed {
            image: url(media/scrollbar/scrollbar_arrowdown_highlight.png);
        }
        """)
        self.menu_bar.set_menus(self.get_menus())

        # 获取最新的讨论
        self.get_latest_discuss()

    def resizeEvent(self, event):
        self.resize_widgets(True)
        if self.detail_warehouse is not None:  # 改变详情控件的大小
            self.detail_warehouse.resize(self.width(), self.height())
        if self.more_dis_widget is not None:
            self.more_dis_widget.setMinimumWidth(self.width() - self.verticalScrollBar().width() - 5)

    def resize_widgets(self, is_loaded):
        if is_loaded:
            width = int(self.parent().width() * 0.618)
            height = int(self.parent().height() * 0.72)
            self.map_view.setFixedSize(width, height)
            self.discuss_show.setFixedHeight(height - self.more_dis_button.height() - 5)  # 减去更多按钮的高度和QFrame横线的高度
            self.contact_channel.resize_map.emit(width, height)  # 调整界面中地图的大小

    def user_reply_discussion(self, discuss_id):
        def commit_discussion():
            content = popup.text_edit.toPlainText().strip()
            try:
                r = requests.post(
                    url=SERVER_API + 'delivery/discussion/',
                    headers={
                        'Content-Type': 'application/json;charset=utf8', 'User-Agent': USER_AGENT,
                        'Authorization': get_user_token()
                    },
                    data=json.dumps({'content': content, 'parent_id': discuss_id})
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 201:
                    raise ValueError(response['detail'])
            except Exception as e:
                QMessageBox.information(popup, '错误', str(e))
            else:
                QMessageBox.information(popup, '成功', response['message'])
                replies = response['replies']
                if self.more_dis_widget is not None:
                    try:
                        self.more_dis_widget.set_replies(replies, discuss_id)
                    except Exception as e:
                        pass
                else:
                    self.discuss_show.set_replies(replies, discuss_id)
                popup.close()
        popup = QDialog(self)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.setWindowTitle('参与讨论')
        popup.resize(350,180)
        layout = QVBoxLayout(popup)
        popup.text_edit = QTextEdit(popup)
        layout.addWidget(popup.text_edit)
        popup.commit_button = QPushButton('提交', popup)
        popup.commit_button.clicked.connect(commit_discussion)
        layout.addWidget(popup.commit_button, alignment=Qt.AlignRight)
        popup.setLayout(layout)
        popup.exec_()

    # 更多讨论交流的页面
    def more_discussion_widget(self):
        # 创建出来,加入主layout
        self.more_dis_widget = MoreDiscussWidget(self)
        self.more_dis_widget.reply_discussion.connect(self.user_reply_discussion)
        self.more_dis_widget.resize(self.width(), self.height())
        # 关闭主layout中的其他控件
        self.map_view.hide()
        self.dis_label.hide()
        self.more_dis_button.hide()
        self.discuss_show.hide()
        self.warehouse_table.hide()
        # 显示更多讨论交流的控件
        self.container.layout().insertWidget(self.container.layout().count() - 1, self.more_dis_widget)
        self.more_dis_widget.show()

    # 删除更多页面
    def delete_more_discussion_widget(self):
        self.map_view.show()
        self.dis_label.show()
        self.more_dis_button.show()
        self.discuss_show.show()
        self.warehouse_table.show()
        if self.more_dis_widget is not None:
            self.more_dis_widget.deleteLater()
            del self.more_dis_widget
            self.more_dis_widget = None

    # 获取最新的讨论交流
    def get_latest_discuss(self):
        try:
            r = requests.get(SERVER_API + 'delivery/discussion-latest/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError('获取最新讨论失败')
        except Exception:
            discuss = []
        else:
            discuss = response['discussions']
        for item_json in discuss:
            item = DiscussItem(item_json)
            self.discuss_show.add_discuss_item(item)

    def get_menus(self):
        menus = [
            {"id": 2,
             "text": "地区",
             "children": [
                 {"id": 1, "name": "北京"},
                 {"id": 2, "name": "天津"},
                 {"id": 3, "name": "上海"},
                 {"id": 4, "name": "重庆"},
                 {"id": 5, "name": "河北"},
                 {"id": 6, "name": "山西"},
                 {"id": 7, "name": "辽宁"},
                 {"id": 8, "name": "吉林"},
                 {"id": 9, "name": "黑龙江"},
                 {"id": 10, "name": "江苏"},
                 {"id": 11, "name": "浙江"},
                 {"id": 12, "name": "安徽"},
                 {"id": 13, "name": "福建"},
                 {"id": 14, "name": "江西"},
                 {"id": 15, "name": "山东"},
                 {"id": 16, "name": "河南"},
                 {"id": 17, "name": "湖北"},
                 {"id": 18, "name": "湖南"},
                 {"id": 19, "name": "广东"},
                 {"id": 20, "name": "海南"},
                 {"id": 21, "name": "四川"},
                 {"id": 22, "name": "贵州"},
                 {"id": 23, "name": "云南"},
                 {"id": 24, "name": "陕西"},
                 {"id": 25, "name": "甘肃"},
                 {"id": 26, "name": "青海"},
                 {"id": 27, "name": "台湾"},
                 {"id": 28, "name": "内蒙古"},
                 {"id": 29, "name": "广西"},
                 {"id": 30, "name": "西藏"},
                 {"id": 31, "name": "宁夏"},
                 {"id": 32, "name": "新疆"},
                 {"id": 33, "name": "香港"},
                 {"id": 34, "name": "澳门"}
             ]
             },
            {
                "id": 3,
                "text": "服务指引",
                "children": {
                    "仓单流程": [{"name": "仓单注册流程"}, {"name": "仓单注销流程"}, {"name": "厂库仓单注册"}],
                    "交割流程": [{"name": "上期所交割流程"}, {"name": "郑商所交割流程"}, {"name": "大商所交割流程"}, {"name": "能源中心交割流程"}],
                    "套期保值": [{"name": "上期所套保业务"}, {"name": "郑商所套保业务"}, {"name": "大商所套保业务"}, {"name": "能源中心套保业务"}]
                }
            }
        ]
        try:
            r = requests.get(
                url=SERVER_API + 'exchange/variety-all/',
                headers={'User-Agent': USER_AGENT}
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            variety_menus = {"id": 1, "text": "品种仓库", 'children': response['varieties']}
            menus.insert(0, variety_menus)
            brand_menus = {"id": 4, "text": "品牌名录", "children": response['varieties']}
            menus.append(brand_menus)
            cost_menus = {"id": 5, "text": "交割费用", "children": response['varieties']}
            menus.append(cost_menus)
            quality_menus = {"id": 6, "text": "质检机构", "children": response['varieties']}
            menus.append(quality_menus)
        finally:
            return menus

    def set_children_menu_layout(self, p_id, child_menus):
        """ 必须重写这个方法，根据id设置子菜单的layout样式 """
        if p_id == 1:
            layout = QVBoxLayout()
            layout.setSpacing(2)
            for exchange, variety_list in child_menus.items():
                exchange_name = variety_list[0]["exchange_name"]
                if exchange in ["cffex", "ine"]:
                    continue
                layout.addWidget(QLabel(exchange_name,
                                        styleSheet='font-size:14px;'
                                                   'font-weight:bold;'
                                                   'background-color:rgb(180,180,180);'
                                                   'padding:3px 0;'
                                                   'border-bottom: 1px solid rgb(30,30,30)'
                                        )
                                 )
                if len(variety_list) > 0:

                    sub_layout = QGridLayout()
                    for index, variety_item in enumerate(variety_list):
                        v_btn = VarietyButton(bid=variety_item['id'], v_en=variety_item['variety_en'],text=variety_item["variety_name"])
                        v_btn.select_variety_menu.connect(self.get_variety_warehouses)
                        sub_layout.addWidget(v_btn, index / 8, index % 8, alignment=Qt.AlignLeft)
                    layout.addLayout(sub_layout)
        elif p_id == 2:
            layout = QGridLayout()
            for index, area_item in enumerate(child_menus):
                area_btn = AreaButton(area_item['name'])
                area_btn.select_area_menu.connect(self.get_province_warehouses)
                layout.addWidget(area_btn, index / 5, index % 5)
        elif p_id == 3:
            layout = QVBoxLayout()
            for header, menu_list in child_menus.items():
                layout.addWidget(QLabel(header,
                                        styleSheet='font-size:14px;'
                                                   'font-weight:bold;'
                                                   'background-color:rgb(180,180,180);'
                                                   'padding:3px 0;'
                                                   'border-bottom: 1px solid rgb(30,30,30)'
                                        )
                                 )
                if len(menu_list) > 0:
                    sub_layout = QGridLayout()
                    sub_layout.setAlignment(Qt.AlignLeft)
                    for index, variety_item in enumerate(menu_list):
                        m_btn = CustomMenuButton(text=variety_item["name"], width=108)
                        m_btn.clicked.connect(self.to_show_service)
                        sub_layout.addWidget(m_btn, index / 3, index % 3)
                    layout.addLayout(sub_layout)
        elif p_id == 4:  # 品牌名录
            layout = QVBoxLayout()
            for exchange, variety_list in child_menus.items():
                exchange_name = variety_list[0]["exchange_name"]
                if exchange in ["cffex", "ine"]:
                    continue
                layout.addWidget(QLabel(exchange_name,
                                        styleSheet='font-size:14px;'
                                                   'font-weight:bold;'
                                                   'background-color:rgb(180,180,180);'
                                                   'padding:3px 0;'
                                                   'border-bottom: 1px solid rgb(30,30,30)'
                                        )
                                 )
                if len(variety_list) > 0:
                    sub_layout = QGridLayout()
                    for index, variety_item in enumerate(variety_list):
                        v_btn = CustomMenuButton(text=variety_item["variety_name"], width=65)
                        v_btn.variety_en = variety_item['variety_en']
                        v_btn.category = 'brand'
                        v_btn.clicked.connect(self.show_target_pdf)
                        sub_layout.addWidget(v_btn, index / 8, index % 8, alignment=Qt.AlignLeft)
                    layout.addLayout(sub_layout)
        elif p_id == 5:  # 交割费用
            layout = QVBoxLayout()
            for exchange, variety_list in child_menus.items():
                if exchange in ["cffex", "ine"]:
                    continue
                exchange_name = variety_list[0]["exchange_name"]
                layout.addWidget(QLabel(exchange_name,
                                        styleSheet='font-size:14px;'
                                                   'font-weight:bold;'
                                                   'background-color:rgb(180,180,180);'
                                                   'padding:3px 0;'
                                                   'border-bottom: 1px solid rgb(30,30,30)'
                                        )
                                 )
                if len(variety_list) > 0:
                    sub_layout = QGridLayout()
                    for index, variety_item in enumerate(variety_list):
                        v_btn = CustomMenuButton(text=variety_item["variety_name"], width=65)
                        v_btn.variety_en = variety_item['variety_en']
                        v_btn.category = 'cost'
                        v_btn.clicked.connect(self.show_target_pdf)
                        sub_layout.addWidget(v_btn, index / 8, index % 8, alignment=Qt.AlignLeft)
                    layout.addLayout(sub_layout)

        elif p_id == 6:  # 质检机构
            layout = QVBoxLayout()
            for exchange, variety_list in child_menus.items():
                if exchange in ["cffex", "ine"]:
                    continue
                exchange_name = variety_list[0]["exchange_name"]
                layout.addWidget(QLabel(exchange_name,
                                        styleSheet='font-size:14px;'
                                                   'font-weight:bold;'
                                                   'background-color:rgb(180,180,180);'
                                                   'padding:3px 0;'
                                                   'border-bottom: 1px solid rgb(30,30,30)'
                                        )
                                 )
                if len(variety_list) > 0:
                    sub_layout = QGridLayout()
                    for index, variety_item in enumerate(variety_list):
                        v_btn = CustomMenuButton(text=variety_item["variety_name"], width=65)
                        v_btn.variety_en = variety_item['variety_en']
                        v_btn.category = 'quality'
                        v_btn.clicked.connect(self.show_target_pdf)
                        sub_layout.addWidget(v_btn, index / 8, index % 8, alignment=Qt.AlignLeft)
                    layout.addLayout(sub_layout)
        else:
            layout = QHBoxLayout()
        return layout

    def show_target_pdf(self):
        btn = self.sender()
        if not btn or not isinstance(btn, QPushButton):
            return
        menu_text = btn.text()
        file_url = "{}DELIVERY/{}/{}{}.pdf".format(STATIC_URL, btn.category, menu_text, btn.variety_en)
        popup = PDFContentPopup(title=menu_text, file=file_url)
        popup.exec_()

    def to_show_service(self):
        btn = self.sender()
        if not btn or not isinstance(btn, QPushButton):
            return
        menu_text = btn.text()
        # 显示各种内容
        if menu_text in [
            "仓单注册流程","仓单注销流程", "厂库仓单注册",
            "上期所交割流程","郑商所交割流程","大商所交割流程","能源中心交割流程",
            "上期所套保业务","郑商所套保业务","大商所套保业务","能源中心套保业务"
        ]:
            file_url = STATIC_URL + 'DELIVERY/' + menu_text + '.pdf'
            popup = PDFContentPopup(title=menu_text, file=file_url)
            popup.exec_()

    def get_variety_warehouses(self, v_id, variety_en):
        self.menu_bar.child_menus_widget.close()
        self.delete_more_discussion_widget()
        # 获取该品种下的所有仓库
        warehouses = self.request_variety_warehouses(variety_en)
        # 数据传入界面
        self.contact_channel.refresh_warehouses.emit(warehouses)
        # 表格显示数据(数据项必须含id)
        self.warehouse_table.variety_warehouse_show(warehouses)

    # 获取品种下的仓库
    def request_variety_warehouses(self,variety_en):
        try:
            r = requests.get(
                url=SERVER_API + '{}/warehouses/'.format(variety_en),
                headers={'User-Agent': USER_AGENT}
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            return []
        else:
            return response['warehouses']

    def get_province_warehouses(self, area):
        if not self.menu_bar.child_menus_widget.isHidden():
            self.menu_bar.child_menus_widget.close()
        self.delete_more_discussion_widget()
        warehouses = self.request_province_warehouses(area)
        # 数据传入界面
        self.contact_channel.refresh_warehouses.emit(warehouses)
        self.warehouse_table.area_warehouse_show(warehouses)

    # 获取省份下的仓库
    def request_province_warehouses(self, area):
        try:
            r = requests.get(
                url=SERVER_API + 'province-warehouse/?province=' + str(area),
                headers={'User-Agent': USER_AGENT}
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            return []
        else:
            return response['warehouses']

    # 双击进入仓库详情
    def warehouse_table_double_clicked(self, row, col):
        warehouse_code = self.warehouse_table.item(row, 0).fixed_code
        current_variety = self.warehouse_table.item(row, 0).variety_en
        self.get_detail_receipts_and_show(warehouse_code, current_variety)

    # 点击显示仓库信息的表格
    def warehouse_table_cell_clicked(self, row, col):
        current_item = self.warehouse_table.currentItem()
        if not current_item:
            return
        current_text = current_item.text()
        if current_text in ['仓单', '详情']:
            warehouse_code = self.warehouse_table.item(row, 0).fixed_code
            current_variety = self.warehouse_table.item(row, 0).variety_en
            self.get_detail_receipts_and_show(warehouse_code, current_variety)

    def get_detail_receipts_and_show(self, warehouse_code, current_variety):
        # print(current_id, current_variety)
        request_url = SERVER_API + 'warehouse/{}/receipt/'.format(warehouse_code)
        if current_variety is not None:
            request_url += '?variety_en=' + str(current_variety)

        warehouses_receipts = self.request_warehouse_receipts(request_url)
        if not warehouses_receipts:
            QMessageBox.information(self, '消息', '该仓库没有相关的仓单信息.')
            return
        self.show_warehouse_detail(warehouses_receipts)

    # 获取仓库详情与仓单(交割的品种和品种的近10日仓单)
    def request_warehouse_receipts(self, url):
        try:
            r = requests.get(url=url, headers={'User-Agent': USER_AGENT})
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            return {}
        else:
            return response['warehouses_receipts']

    # 显示仓库详情（品种信息、仓单信息等）
    def show_warehouse_detail(self, warehouses_receipts):
        self.show_detail_warehouse(warehouses_receipts)

    def show_detail_warehouse(self, warehouses_receipts):
        self.detail_warehouse = DetailWarehouseReceipts(warehouses_receipts, self)
        self.detail_warehouse.closed_signal.connect(self.detail_warehouse_widget_closed)
        self.detail_warehouse.resize(self.width(), self.height())
        self.verticalScrollBar().hide()

        self.detail_warehouse.detail_animation.setStartValue(QRect(0, self.height(), self.width(), self.height()))
        self.detail_warehouse.detail_animation.setEndValue(QRect(0, 0, self.width(), self.height()))
        self.detail_warehouse.detail_animation.start()
        self.detail_warehouse.show()

    def detail_warehouse_widget_closed(self):  # 关闭详情控件
        self.verticalScrollBar().show()
        if self.detail_warehouse is not None:
            # 关闭的动画
            self.detail_warehouse.detail_animation.setStartValue(QRect(0, 0, self.width(), self.height()))
            self.detail_warehouse.detail_animation.setEndValue(QRect(0, self.height(), self.width(), self.height()))
            self.detail_warehouse.detail_animation.start()
            self.detail_warehouse.show()
            # 关联动画结束
            self.detail_warehouse.detail_animation.finished.connect(self.detail_widget_closed_finished)

    def detail_widget_closed_finished(self):
        # print('关闭动画结束，删除控件，释放内存')
        self.detail_warehouse.close()
        self.detail_warehouse.deleteLater()
        del self.detail_warehouse
        self.detail_warehouse = None

    # 界面点击仓库点
    def get_warehouse_receipts(self, wh_id):
        request_url = SERVER_ADDR + 'warehouse/' + str(wh_id) + '/receipt/'
        warehouses_receipts = self.request_warehouse_receipts(request_url)
        if not warehouses_receipts:
            QMessageBox.information(self, '消息', '该仓库没有相关的仓单信息.')
            return
        self.show_warehouse_detail(warehouses_receipts)
