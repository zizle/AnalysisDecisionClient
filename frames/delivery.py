# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-27
# ------------------------
import os
import json
import requests
from collections import OrderedDict
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,QGridLayout, QFrame, QTableWidget, \
    QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import QMargins, QUrl, Qt, pyqtSignal, QPoint, QSize, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from channels.delivery import WarehouseMapChannel
from widgets import CAvatar
from settings import BASE_DIR, SERVER_ADDR, USER_AGENT


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
        self.setWindowOpacity(0.8)
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
        self.clicked.connect(self.mouse_clicked)

    def mouse_clicked(self):
        self.select_variety_menu.emit(self.bid, self.v_en)


# 地区按钮菜单
class AreaButton(QPushButton):
    select_area_menu = pyqtSignal(str)

    def __init__(self, *args):
        super(AreaButton, self).__init__(*args)
        self.clicked.connect(self.mouse_clicked)

    def mouse_clicked(self):
        self.select_area_menu.emit(self.text())


""" 交流与讨论相关 """


# 回复的项目
class ReplyItem(QWidget):
    def __init__(self,reply_item, *args, **kwargs):
        super(ReplyItem, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        reply_layout = QVBoxLayout(self)
        user_layout = QHBoxLayout(self)
        avatar = CAvatar(size=QSize(20, 20), parent=self)
        user_layout.addWidget(avatar)
        user_layout.addWidget(QLabel(reply_item['username'], self))
        user_layout.addStretch()
        user_layout.addWidget(QLabel("2020-05-28", self))
        reply_layout.addLayout(user_layout)
        text_label = QLabel(self)
        text_label.setText(reply_item['text'])
        reply_layout.addWidget(text_label)
        self.setLayout(reply_layout)

# 讨论的项目
class DiscussItem(QWidget):
    def __init__(self, discuss,*args, **kwargs):
        super(DiscussItem, self).__init__(*args, **kwargs)
        self.replies = discuss['replies']
        self.is_show_replies = False  # 记录是否已经展开了回复
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,0,0,0))
        layout.setSpacing(1)

        discuss_title = QWidget(self)
        discuss_title.setFixedHeight(22)
        username_layout = QHBoxLayout(self)
        username_layout.setContentsMargins(QMargins(2,1,1,1))
        self.avatar = CAvatar(url=discuss['avatar'],size=QSize(20,20), parent=self)
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
        self.reply_button = QPushButton('讨论(' + str(len(self.replies)) + ')', self)
        self.reply_button.setCursor(Qt.PointingHandCursor)
        self.reply_button.clicked.connect(self.show_replies)
        layout.addWidget(self.reply_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

        self.reply_button.setObjectName('replyBtn')
        self.text_show.setObjectName('textLable')
        discuss_title.setObjectName('disTitle')
        self.setStyleSheet("""
        #disTitle{background-color:rgb(150,200,210)}
        #textLable{background-color:rgb(240,240,240);}
        #replyBtn{border:none}
        """)

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

    # 关闭回复
    def close_replies(self):
        for index in range(self.layout().count()):
            widget = self.layout().itemAt(index).widget()
            if isinstance(widget, ReplyItem):
                widget.close()
                widget.deleteLater()
                del widget
        self.is_show_replies = False


# 交流与讨论的控件
class DiscussWidget(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(DiscussWidget, self).__init__(*args, **kwargs)
        self.dis_container = QWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,0,0,0))
        # 具体交流与讨论的项目
        self.dis_container.setLayout(layout)
        self.setWidget(self.dis_container)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dis_container.setLayout(layout)
        self.setObjectName("disScroll")
        self.setStyleSheet("""
        #disScroll{border:none}
        """)

    def add_discuss_item(self, item):
        item.setParent(self)
        self.dis_container.layout().addWidget(item)


# 显示仓库的表格
class WarehouseTable(QTableWidget):
    def __init__(self, *args):
        super(WarehouseTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionBehavior(QHeaderView.SelectRows)
        self.setEditTriggers(QHeaderView.NoEditTriggers)

    # 以地区获取仓库信息的显示方式
    def area_warehouse_show(self, warehouses):
        table_headers = ["地区", "交割仓库", "地址", "交割品种", "查看"]
        self.clear()
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(warehouses))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(warehouses):
            self.setRowHeight(row, 30)
            item0 = QTableWidgetItem(row_item['area'])
            item0.id = row_item['id']
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
            self.setItem(row, 4, item4)
        self.setFixedHeight(self.rowCount() * 30 + 35)

    # 以品种获取仓库的显示方式
    def variety_warehouse_show(self, warehouses):
        self.clear()
        table_headers = ["品种", "交割仓库", "地址", "联系人", "联系方式", "升贴水", "查看"]
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(warehouses))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(warehouses):
            self.setRowHeight(row,30)
            item0 = QTableWidgetItem(row_item['variety'])
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
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
            item6.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 6, item6)
        self.setFixedHeight(self.rowCount() * 30 + 35)


class DetailWarehouseReceipts(QWidget):
    def __init__(self, warehouses_receipts, *args, **kwargs):
        super(DetailWarehouseReceipts, self).__init__(*args, **kwargs)
        print(warehouses_receipts)
        layout = QVBoxLayout(self)
        info_layout = QHBoxLayout(self)
        info_layout.addStretch()
        info_layout.addWidget(QLabel('仓库名称:', self), alignment=Qt.AlignLeft)
        info_layout.addWidget(QLabel(warehouses_receipts['warehouse']))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        for variety_item in warehouses_receipts['varieties']:
            info_layout = QHBoxLayout(self)

            info_layout.addWidget(QLabel('<div>品&nbsp;&nbsp;种:</div>',self, objectName='infoLabel'), alignment=Qt.AlignLeft)
            info_layout.addWidget(QLabel(variety_item['name'], self, objectName='infoMsg'))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>联 系 人:</div>',self, objectName='infoLabel'), alignment=Qt.AlignLeft)
            info_layout.addWidget(QLabel(variety_item['linkman'], self, objectName='infoMsg'))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>联系方式:</div>', self, objectName='infoLabel'), alignment=Qt.AlignLeft)
            info_layout.addWidget(QLabel(variety_item['links'], self, objectName='infoMsg'))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            info_layout = QHBoxLayout(self)
            info_layout.addWidget(QLabel('<div>升 贴 水:</div>',self, objectName='infoLabel'), alignment=Qt.AlignLeft)
            info_layout.addWidget(QLabel(variety_item['premium'], self, objectName='infoMsg'))
            info_layout.addStretch()
            layout.addLayout(info_layout)

            layout.addWidget(QLabel('【仓单信息】', self, objectName='receiptLabel'))
            receipt_table = QTableWidget(self)
            receipt_table.setColumnCount(3)
            receipt_table.setHorizontalHeaderLabels(['日期', '仓单', '增减'])

            for row, receipt_item in enumerate(variety_item['receipts']):
                receipt_table.insertRow(row)
                item0 = QTableWidgetItem(receipt_item['date'])
                item0.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 0, item0)
                item1 = QTableWidgetItem(str(receipt_item['receipt']))
                item1.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 1, item1)
                item2 = QTableWidgetItem(str(receipt_item['increase']))
                item2.setTextAlignment(Qt.AlignCenter)
                receipt_table.setItem(row, 2, item2)

            layout.addWidget(receipt_table)

        layout.addStretch()

        self.setLayout(layout)

        self.setStyleSheet("""
        #infoLabel{font-size:14px;font-weight:bold}
        #infoMsg{font-size:14px}
        """)


class DeliveryPage(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(DeliveryPage, self).__init__(*args, *kwargs)
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

        self.map_view = QWebEngineView(self)
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
        dis_layout.setContentsMargins(QMargins(0,0,0,0))
        dis_layout.setSpacing(1)
        dis_title_layout = QHBoxLayout(self)
        dis_title_layout.setContentsMargins(QMargins(0,0,0,0))
        self.dis_label = QLabel('【最新讨论】', self)
        dis_title_layout.addWidget(self.dis_label, alignment=Qt.AlignLeft)
        self.more_dis_button = QPushButton('更多>>', self)
        self.more_dis_button.setCursor(Qt.PointingHandCursor)
        dis_title_layout.addWidget(self.more_dis_button, alignment=Qt.AlignRight)
        dis_layout.addLayout(dis_title_layout)

        self.discuss_show = DiscussWidget(self)
        dis_layout.addWidget(self.discuss_show)

        map_discuss_layout.addLayout(dis_layout)

        layout.addLayout(map_discuss_layout)

        self.warehouse_table = WarehouseTable(self)
        self.warehouse_table.cellClicked.connect(self.warehouse_table_cell_clicked)
        layout.addWidget(self.warehouse_table)

        self.no_data_label = QLabel('没有数据', self)
        # layout.addWidget(self.no_data_label)
        # 显示仓库详情的控件
        self.detail_warehouse = None
        layout.addStretch()

        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self.more_dis_button.setObjectName('moreDisBtn')
        self.setStyleSheet("""
        #moreDisBtn{border:none}
        """)

        self.menu_bar.set_menus(self.get_menus())

    def resizeEvent(self, event):
        self.resize_widgets(True)

    def resize_widgets(self, is_loaded):
        if is_loaded:
            width = int(self.parent().width() * 0.618)
            height = int(self.parent().height() * 0.72)
            self.map_view.setFixedSize(width, height)
            self.discuss_show.setFixedHeight(height - self.more_dis_button.height() - 5)  # 减去更多按钮的高度和QFrame横线的高度
            self.contact_channel.resize_map.emit(width, height)  # 调整界面中地图的大小

    # 获取最新的讨论交流
    def get_hot_discuss(self):
        discuss = [
            {
                'avatar': '',
                'username': '用户名',
                'create_time': '2020-05-28',
                'text': '这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容，这是内容',
                'replies': [
                    {'avatar': '', 'username': '用户名', 'text': '回复的内容', 'create_time': '2020-05-28'}
                ]
            },
            {
                'avatar': '',
                'username': '用户名',
                'create_time': '2020-05-29',
                'text': '这是内容2，这是内容2，这是内容2，这是内容2，',
                'replies': [
                    {'avatar': '', 'username': '用户名', 'text': '回复的内容', 'create_time': '2020-05-28'},
                    {'avatar': '', 'username': '用户名', 'text': '回复的内容', 'create_time': '2020-05-28'},
                    {'avatar': '', 'username': '用户名', 'text': '回复的内容', 'create_time': '2020-05-28'}
                ]
            },
            {
                'avatar': '',
                'username': '用户名',
                'create_time': '2020-05-29',
                'text': '这是内容2，这是内容2，这是内容2，这是内容2，这是内容2，这是内容2，这是内容2，这是内容2，',
                'replies': [
                    {'avatar': '', 'username': '用户名', 'text': '回复的内容', 'create_time': '2020-05-28'}
                ]
            },


        ]
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
                "children": []
            }
        ]
        try:
            r = requests.get(
                url=SERVER_ADDR + 'variety/?way=exchange',
                headers={'User-Agent': USER_AGENT}
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            variety_menus = {"id": 1, "text": "品种", 'children': response['variety']}
            menus.insert(0, variety_menus)
        finally:
            return menus

    def set_children_menu_layout(self, p_id, child_menus):
        """ 必须重写这个方法，根据id设置子菜单的layout样式 """
        if p_id == 1:
            layout = QVBoxLayout()
            for exchange, variety_list in child_menus.items():
                if exchange == "中国金融期货交易所":
                    continue
                layout.addWidget(QLabel(exchange))
                if len(variety_list) > 0:
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    layout.addWidget(line)
                    sub_layout = QGridLayout()
                    for index, variety_item in enumerate(variety_list):
                        v_btn = VarietyButton(bid=variety_item['id'], v_en=variety_item['name_en'],text=variety_item["name"])
                        v_btn.select_variety_menu.connect(self.get_variety_warehouses)
                        sub_layout.addWidget(v_btn, index / 2, index % 2, alignment=Qt.AlignLeft)
                    layout.addLayout(sub_layout)
        elif p_id == 2:
            layout = QGridLayout()
            for index, area_item in enumerate(child_menus):
                area_btn = AreaButton(area_item['name'])
                area_btn.select_area_menu.connect(self.get_province_warehouses)
                layout.addWidget(area_btn, index / 5, index % 5)
        else:
            layout = QHBoxLayout()
        return layout

    def get_variety_warehouses(self, v_id, variety_en):
        self.hide_detail_warehouse()
        self.menu_bar.child_menus_widget.close()
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
                url=SERVER_ADDR + 'variety/warehouse/?v_en=' + str(variety_en),
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
        self.hide_detail_warehouse()
        if not self.menu_bar.child_menus_widget.isHidden():
            self.menu_bar.child_menus_widget.close()
        warehouses = self.request_province_warehouses(area)
        # 数据传入界面
        self.contact_channel.refresh_warehouses.emit(warehouses)
        self.warehouse_table.area_warehouse_show(warehouses)

    # 获取省份下的仓库
    def request_province_warehouses(self, area):
        try:
            r = requests.get(
                url=SERVER_ADDR + 'province/warehouse/?province=' + str(area),
                headers={'User-Agent': USER_AGENT}
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            return []
        else:
            return response['warehouses']

    # 点击显示仓库信息的表格
    def warehouse_table_cell_clicked(self, row, col):
        current_item = self.warehouse_table.currentItem()
        if not current_item:
            return
        current_text = current_item.text()
        if current_text in ['仓单', '详情']:
            current_id = self.warehouse_table.item(row, 0).id
            current_variety = self.warehouse_table.item(row, 0).variety_en
            print(current_id, current_variety)
            request_url = SERVER_ADDR + 'warehouse/' + str(current_id) + '/receipts/'
            if current_variety is not None:
                request_url += '?v_en=' + str(current_variety)

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
            print(e)
            return {}
        else:
            return response['warehouses_receipts']

    # 显示仓库详情（品种信息、仓单信息等）
    def show_warehouse_detail(self, warehouses_receipts):
        self.show_detail_warehouse(warehouses_receipts)

    def show_detail_warehouse(self, warehouses_receipts):
        self.detail_warehouse = DetailWarehouseReceipts(warehouses_receipts, self)
        self.container.layout().insertWidget(self.container.layout().count()-1, self.detail_warehouse)
        self.map_view.hide()
        self.discuss_show.hide()
        self.warehouse_table.hide()
        self.dis_label.hide()
        self.more_dis_button.hide()
        self.no_data_label.hide()

    def hide_detail_warehouse(self):
        if self.detail_warehouse is not None:
            self.detail_warehouse.close()
            self.map_view.show()
            self.discuss_show.show()
            if self.warehouse_table.rowCount() == 0:
                self.no_data_label.show()
            else:
                self.warehouse_table.show()
            self.dis_label.show()
            self.more_dis_button.show()
            self.detail_warehouse.deleteLater()
            self.detail_warehouse = None


    # 界面点击仓库点
    def get_warehouse_receipts(self, wh_id):
        print(wh_id)
