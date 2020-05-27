# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-27
# ------------------------
import os
import json
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,QGridLayout, QFrame, QTableWidget, \
    QTableWidgetItem, QHeaderView
from PyQt5.QtCore import QMargins, QUrl, Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from channels.delivery import WarehouseMapChannel
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


class DeliveryPage(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(DeliveryPage, self).__init__(*args, *kwargs)
        self.container = QWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        layout.setSpacing(1)
        map_discuss_layout = QHBoxLayout(self)
        map_discuss_layout.setContentsMargins(QMargins(0,0,0,0))
        self.menu_bar = MenuBar(self)
        self.menu_bar.set_parent(self)
        layout.addWidget(self.menu_bar, alignment=Qt.AlignTop)

        self.map_view = QWebEngineView(self)
        self.map_view.load(QUrl("file:///pages/delivery/map.html"))

        channel_qt_obj = QWebChannel(self.map_view.page())  # 实例化qt信道对象,必须传入页面参数
        self.contact_channel = WarehouseMapChannel()  # 页面信息交互通道
        self.contact_channel.request_province_warehouses.connect(self.get_province_warehouses)
        self.contact_channel.request_warehouse_detail.connect(self.get_warehouse_receipts)
        # self.contact_channel.receivedUserTokenBack.connect(self.web_has_received_token)  # 收到token的回馈
        # self.contact_channel.moreCommunicationSig.connect(self.more_communication)  # 更多讨论交流页面
        # self.contact_channel.linkUsPageSig.connect(self.to_link_us_page)  # 关于我们的界面
        # self.contact_channel.getInfoFile.connect(self.get_information_file)  # 弹窗显示品种的相关PDF文件
        self.map_view.page().setWebChannel(channel_qt_obj)
        channel_qt_obj.registerObject("pageContactChannel", self.contact_channel)  # 信道对象注册信道，只能注册一个

        map_discuss_layout.addWidget(self.map_view, alignment=Qt.AlignTop)

        map_discuss_layout.addWidget(QLabel('交流与讨论区'))

        layout.addLayout(map_discuss_layout)

        self.warehouse_table = QTableWidget(self)

        layout.addWidget(self.warehouse_table)
        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.menu_bar.set_menus(self.get_menus())

    def resizeEvent(self, event):
        width = int(self.width() * 0.618)
        height = int(self.height() * 0.72)
        self.map_view.setFixedSize(width, height)
        self.contact_channel.resize_map.emit(width, height)

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

    def warehouse_table_show(self, warehouses):
        # print(warehouses)
        table_headers = ["品种", "交割仓库", "地址", "联系人", "联系方式", "升贴水", "查看"]
        self.warehouse_table.setColumnCount(len(table_headers))
        self.warehouse_table.setRowCount(len(warehouses))
        self.warehouse_table.setHorizontalHeaderLabels(table_headers)
        self.warehouse_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.warehouse_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(warehouses):
            item0 = QTableWidgetItem(row_item['variety'])
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.v_en = row_item['variety_en']
            self.warehouse_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['name'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['addr'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['linkman'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['links'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['premium'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 5, item5)
            item6 = QTableWidgetItem('仓单')
            item6.setTextAlignment(Qt.AlignCenter)
            self.warehouse_table.setItem(row, 6, item6)

    # 品种菜单选择了品种
    def get_variety_warehouses(self, v_id, variety_en):
        self.menu_bar.child_menus_widget.close()
        # 获取该品种下的所有仓库
        warehouses = self.request_variety_warehouses(variety_en)
        # 数据传入界面
        self.contact_channel.refresh_warehouses.emit(warehouses)
        # 表格显示数据
        self.warehouse_table_show(warehouses)

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

    # 地区菜单选择了地区
    def get_province_warehouses(self, area):
        if not self.menu_bar.child_menus_widget.isHidden():
            self.menu_bar.child_menus_widget.close()
        warehouses = self.request_province_warehouses(area)
        # 数据传入界面
        self.contact_channel.refresh_warehouses.emit(warehouses)
        print(warehouses)

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

    # 获取仓库详情与仓单
    def get_warehouse_receipts(self, wh_id):
        print(wh_id)
