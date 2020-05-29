# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
import json
import requests
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget,QGridLayout, QLabel, QPushButton,QTableWidget, QLineEdit, \
    QComboBox, QMessageBox,QTableWidgetItem, QFrame, QHeaderView, QMenu, QDialog
from PyQt5.QtCore import Qt, QMargins, QPoint, pyqtSignal
from PyQt5.QtGui import QCursor
from widgets import LoadedPage

from settings import SERVER_ADDR, USER_AGENT


"""仓库管理"""


class CreateNewWarehouse(QWidget):
    def __init__(self, *args, **kwargs):
        super(CreateNewWarehouse, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        edit_layout = QGridLayout(self)

        edit_layout.addWidget(QLabel('编码:', self), 0, 0)
        self.fixed_code_edit = QLineEdit(self)
        self.fixed_code_edit.setPlaceholderText('输入仓库编码,4位数字符串。例如：0001')
        edit_layout.addWidget(self.fixed_code_edit, 0, 1)

        edit_layout.addWidget(QLabel('地区:', self), 1, 0)
        self.area_edit = QLineEdit(self)
        edit_layout.addWidget(self.area_edit, 1, 1)

        edit_layout.addWidget(QLabel('名称:', self), 2, 0)
        self.name_edit = QLineEdit(self)
        edit_layout.addWidget(self.name_edit, 2, 1)

        edit_layout.addWidget(QLabel('简称:', self), 3, 0)
        self.short_name_edit = QLineEdit(self)
        self.short_name_edit.setPlaceholderText('简称需与交易所公布的一致!')
        edit_layout.addWidget(self.short_name_edit, 3, 1)

        edit_layout.addWidget(QLabel('地址:', self), 4, 0)
        self.addr_edit = QLineEdit(self)
        edit_layout.addWidget(self.addr_edit, 4, 1)

        edit_layout.addWidget(QLabel('经度:', self), 5, 0)
        self.lng_edit = QLineEdit(self)
        edit_layout.addWidget(self.lng_edit, 5, 1)

        edit_layout.addWidget(QLabel('经度:', self), 6, 0)
        self.lat_edit = QLineEdit(self)
        edit_layout.addWidget(self.lat_edit, 6, 1)

        layout.addLayout(edit_layout)

        self.commit_button = QPushButton('提交', self)
        self.commit_button.clicked.connect(self.commit_new_warehouse)
        layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        layout.addStretch()

        self.setLayout(layout)

    def hide(self):
        self.clear_edit()
        super(CreateNewWarehouse, self).hide()

    def clear_edit(self):
        self.area_edit.setText('')
        self.name_edit.setText('')
        self.short_name_edit.setText('')
        self.addr_edit.setText('')
        self.lng_edit.setText('')
        self.lat_edit.setText('')

    def commit_new_warehouse(self):
        # 整理数据
        fixed_code = self.fixed_code_edit.text().strip()
        area = self.area_edit.text().strip()
        name = self.name_edit.text().strip()
        short_name = self.short_name_edit.text().strip()
        addr = self.addr_edit.text().strip()
        longitude = self.lng_edit.text().strip()
        latitude = self.lat_edit.text().strip()
        if not all([fixed_code, area, name,short_name, addr, longitude, latitude]):
            QMessageBox.information(self, '错误', '有字段未填写完整!')
            return
        try:
            r = requests.post(
                url=SERVER_ADDR + 'warehouse/',
                headers={'Content-Type':'application/json;','User-Agent':USER_AGENT},
                data=json.dumps({
                    'fixed_code': fixed_code,
                    'area': area,
                    'name': name,
                    'short_name': short_name,
                    'addr': addr,
                    'longitude': float(longitude),
                    'latitude': float(latitude)
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.clear_edit()


class WarehouseTable(QTableWidget):
    action_signal = pyqtSignal(int, str)

    def __init__(self, *args):
        super(WarehouseTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QHeaderView.NoEditTriggers)
        self.setSelectionBehavior(QHeaderView.SelectRows)

    def mousePressEvent(self, event):
        super(WarehouseTable, self).mousePressEvent(event)
        if event.buttons() != Qt.RightButton:
            return
        index = self.indexAt(QPoint(event.x(), event.y()))
        current_row = index.row()
        self.setCurrentIndex(index)
        if current_row < 0:
            return

        menu = QMenu()
        variety_manager = menu.addAction("交割品种管理")
        variety_manager.triggered.connect(self.manger_delivery_variety)
        menu.exec_(QCursor.pos())

    def manger_delivery_variety(self):
        house_id = self.item(self.currentRow(), 0).id
        self.action_signal.emit(house_id, "交割品种管理")

    def show_warehouses(self, house_list):
        table_headers = ['编号', '地区','名称', '简称', '地址', '增加日期']
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.setRowCount(len(house_list))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, row_item in enumerate(house_list):
            item0 = QTableWidgetItem(row_item['fixed_code'])
            item0.id = row_item['id']
            item0.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['area'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['name'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['short_name'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['addr'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['create_time'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)


class WarehouseVarietyManager(QWidget):
    def __init__(self, house_id, *args, **kwargs):
        super(WarehouseVarietyManager, self).__init__(*args, **kwargs)
        self.house_id = house_id
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0,2,1,0))
        layout.setSpacing(2)
        self.house_msg = QLabel(self)
        layout.addWidget(self.house_msg, alignment=Qt.AlignLeft)
        self.manger_table = QTableWidget(self)
        self.manger_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.manger_table.setSelectionBehavior(QHeaderView.SelectRows)
        self.manger_table.setFrameShape(QFrame.NoFrame)
        self.manger_table.cellChanged.connect(self.manager_table_checked_changed)
        layout.addWidget(self.manger_table)

        self.setLayout(layout)

    # 获取当前仓库的信息和交割品种
    def get_current_house_message(self):
        try:
            r = requests.get(url=SERVER_ADDR + 'warehouse/' + str(self.house_id) + '/variety/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.house_msg.setText(str(e))
        else:
            print(response)
            self.house_msg.setText("仓库:【" + response['name'] + "】 简称:" + response['short_name'])
            self.table_show_content(response['result'])

    def table_show_content(self, contents):
        self.manger_table.cellChanged.disconnect()
        self.manger_table.clear()
        table_headers = ['品种', '代码', '是否交割']
        self.manger_table.setColumnCount(len(table_headers))
        self.manger_table.setRowCount(len(contents))
        self.manger_table.setHorizontalHeaderLabels(table_headers)
        self.manger_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(contents):
            item0 = QTableWidgetItem(row_item['name'])
            item0.id = row_item['id']
            item0.setTextAlignment(Qt.AlignCenter)
            self.manger_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['name_en'])
            if row_item['is_delivery']:
                item2 = QTableWidgetItem('有交割')
                item2.setCheckState(Qt.Checked)
            else:
                item2 = QTableWidgetItem('无交割')
                item2.setCheckState(Qt.Unchecked)
            item1.setTextAlignment(Qt.AlignCenter)
            item2.setTextAlignment(Qt.AlignCenter)
            self.manger_table.setItem(row, 1, item1)
            self.manger_table.setItem(row, 2, item2)
        self.manger_table.cellChanged.connect(self.manager_table_checked_changed)

    def manager_table_checked_changed(self, row, col):
        def commit_new_delivery_variety():
            print('新增交割品种')
            print(self.house_id, variety_en, checked)
            delivery_msg = {
                "linkman": popup.linkman_edit.text().strip(),
                "links": popup.links_edit.text().strip(),
                "premium": popup.premium_edit.text().strip()
            }
            request_d = {
                "house_id": self.house_id,
                "variety_text": variety_text,
                "variety_en": variety_en,
                "is_delivery": checked,
                "delivery_msg": delivery_msg,
            }
            send_request(request_d)

        def send_request(data):
            try:
                r = requests.post(
                    url=SERVER_ADDR + 'warehouse/' + str(data['house_id']) + '/variety/',
                    headers={'Content-Type':'application/json;charset=utf8', 'User-Agent': USER_AGENT},
                    data=json.dumps(data)
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(self, '错误', str(e))
            else:
                QMessageBox.information(self, '成功', response['message'])
                if checked == 1:
                    popup.close()
        if col != 2:
            return
        variety_text = self.manger_table.item(row, 0).text()
        variety_en = self.manger_table.item(row, 1).text()
        check_item = self.manger_table.item(row, col)
        checked = 0
        if check_item.checkState() == Qt.Checked:  # 当前的选中状态(目标状态)
            checked = 1
            # 弹窗设置内容(联系人,联系方式,升贴水)
            popup = QDialog(self)
            popup.setAttribute(Qt.WA_DeleteOnClose)
            popup.setWindowTitle("交割基础信息")
            layout = QGridLayout(popup)
            layout.addWidget(QLabel('联系人:', popup), 0, 0)
            popup.linkman_edit = QLineEdit(popup)
            layout.addWidget(popup.linkman_edit, 0, 1)

            layout.addWidget(QLabel('联系方式:', popup), 1, 0)
            popup.links_edit = QLineEdit(popup)
            layout.addWidget(popup.links_edit, 1, 1)

            layout.addWidget(QLabel('升贴水:', popup), 2, 0)
            popup.premium_edit = QLineEdit(popup)
            layout.addWidget(popup.premium_edit, 2, 1)
            popup.setLayout(layout)

            popup.commit_button = QPushButton('确定', popup)
            popup.commit_button.clicked.connect(commit_new_delivery_variety)
            layout.addWidget(popup.commit_button, 3, 0, 1, 2)
            popup.exec_()

        else:
            send_request({
                "house_id": self.house_id,
                "variety_text": variety_text,
                "variety_en": variety_en,
                "is_delivery": checked,
                "delivery_msg": {},
            })


class WarehouseAdmin(QWidget):
    table_actions_signal = pyqtSignal(int, str)

    def __init__(self, *args, **kwargs):
        super(WarehouseAdmin, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 1, 0))
        self.switch_button = QPushButton('新增仓库', self)
        self.switch_button.clicked.connect(self.switch_option)
        layout.addWidget(self.switch_button, alignment=Qt.AlignLeft)

        self.warehouse_table = WarehouseTable(self)
        self.warehouse_table.action_signal.connect(self.table_actions_signal)
        layout.addWidget(self.warehouse_table)

        self.new_warehouse = CreateNewWarehouse(self)
        self.new_warehouse.hide()
        layout.addWidget(self.new_warehouse)
        self.setLayout(layout)

    def switch_option(self):
        if self.switch_button.text() == '新增仓库':
            self.warehouse_table.hide()
            self.new_warehouse.show()
            self.switch_button.setText('所有仓库')
        else:
            self.warehouse_table.show()
            self.new_warehouse.hide()
            self.switch_button.setText('新增仓库')
            self.get_warehouses()

    def get_warehouses(self):
        try:
            r = requests.get(url=SERVER_ADDR + 'warehouse/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            pass
        else:
            self.warehouse_table.show_warehouses(response['warehouses'])


# 交割服务维护主页
class DeliveryInfoAdmin(QWidget):
    def __init__(self, *args, **kwargs):
        super(DeliveryInfoAdmin, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 1, 0))
        layout.setSpacing(0)
        self.menu_list = QListWidget(self)
        self.menu_list.addItems(["仓库管理"])
        self.menu_list.clicked.connect(self.clicked_left_menu)
        layout.addWidget(self.menu_list, alignment=Qt.AlignLeft)

        self.right_frame = LoadedPage(self)
        self.right_frame.remove_borders()
        layout.addWidget(self.right_frame)

        self.setLayout(layout)

        self.menu_list.setObjectName('leftList')
        self.setStyleSheet("""
        #leftList{
            outline:none;
            border:none;
            border-right: 1px solid rgb(180,180,180);
            background-color: rgb(240,240,240);
        }
        #leftList::item{
           height:25px;
        }
        #leftList::item:selected{
           border-left:3px solid rgb(100,120,150);
           color:#000;
           background-color:rgb(180,220,230);
        }
        """)

    def clicked_left_menu(self):
        menu = self.menu_list.currentItem().text()
        print(menu)
        if menu == '仓库管理':
            page = WarehouseAdmin()
            page.table_actions_signal.connect(self.sub_actions_go)
            page.get_warehouses()
        else:
            page = QLabel('【' + menu + '】正在加紧开发中...')

        self.right_frame.clear()
        self.right_frame.addWidget(page)

    def sub_actions_go(self, item_id, action_text):
        print(item_id, action_text)
        if action_text == '交割品种管理':
            page = WarehouseVarietyManager(item_id)
            page.get_current_house_message()
        else:
            page = QLabel('【' + action_text + '】没有此项功能...')
        self.right_frame.clear()
        self.right_frame.addWidget(page)