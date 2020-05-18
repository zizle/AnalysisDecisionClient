# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import re
import json
import requests
from urllib3 import encode_multipart_formdata
from PyQt5.QtWidgets import QWidget, QListWidget, QHBoxLayout, QVBoxLayout,QMessageBox, QTabWidget, QLabel, QComboBox, QGridLayout, \
    QHeaderView, QPushButton, QTableWidgetItem, QLineEdit, QAbstractItemView, QTableWidget, QDialog, QMenu
from PyQt5.QtCore import Qt, QPoint, QMargins
from PyQt5.QtGui import QCursor, QIcon, QColor, QBrush, QPixmap, QImage
from widgets import PDFContentPopup, ImagePathLineEdit, FilePathLineEdit
import settings

"""用户管理"""


class VarietyAuthDialog(QDialog):
    def __init__(self, user_id, *args):
        super(VarietyAuthDialog, self).__init__(*args)
        self.user_id = user_id
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("用户品种权限")
        self.setWindowIcon(QIcon("media/logo.png"))
        self.setFixedSize(1000, 600)
        layout = QVBoxLayout()
        layout.setParent(self)
        self.user_info_label = QLabel(self)
        layout.addWidget(self.user_info_label)
        self.variety_table = QTableWidget(self)
        self.variety_table.verticalHeader().hide()
        self.variety_table.cellClicked.connect(self.clickedCell_variety_table)
        layout.addWidget(self.variety_table)
        self.setLayout(layout)

    def get_varieties(self):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/?way=group')
            response = json.loads(r.content.decode('utf8'))
        except Exception as e:
            pass
        else:
            self.setVarietyContents(response['variety'])

    def setVarietyContents(self, row_contents):
        self.variety_table.clear()
        table_headers = ['序号', '品种', '权限']
        self.variety_table.setColumnCount(len(table_headers))
        self.variety_table.setHorizontalHeaderLabels(table_headers)
        self.variety_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.variety_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        current_row = 0
        for row_item in row_contents:
            self.variety_table.insertRow(current_row)
            item0 = QTableWidgetItem(str(current_row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.variety_table.setItem(current_row, 0, item0)
            item1 = QTableWidgetItem(row_item['name'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.variety_table.setItem(current_row, 1, item1)
            for variety_item in row_item['subs']:
                current_row += 1
                self.variety_table.insertRow(current_row)
                item0 = QTableWidgetItem(str(current_row + 1))
                item0.setTextAlignment(Qt.AlignCenter)
                item0.id = variety_item['id']
                self.variety_table.setItem(current_row, 0, item0)
                item1 = QTableWidgetItem(variety_item['name'])
                item1.setTextAlignment(Qt.AlignCenter)
                self.variety_table.setItem(current_row, 1, item1)
                item2 = QTableWidgetItem("点击开启")
                item2.setTextAlignment(Qt.AlignCenter)
                item2.setForeground(QBrush(QColor(250,50,50)))
                self.variety_table.setItem(current_row, 2, item2)
            current_row += 1

    def getCurrentUserAccessVariety(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/' + str(self.user_id) + '/variety/'
            )
            response = json.loads(r.content.decode('utf8'))
        except Exception as e:
            pass
        else:
            user_info = response['user_info']
            userinfo_text = "用户名:" + user_info['username'] + '\t' + "手机:" + user_info['phone']
            self.setWindowTitle("【"+user_info["username"]+"】品种权限")
            self.user_info_label.setText(userinfo_text)
            # 修改权限的状态
            for variety_item in response['variety']:
                for row in range(self.variety_table.rowCount()):
                    row_vid = self.variety_table.item(row, 0).id
                    if row_vid == variety_item['variety_id'] and variety_item['is_active']:
                        item = self.variety_table.item(row, 2)
                        if item:
                            item.setText("点击关闭")
                            item.setForeground(QBrush(QColor(50,250,50)))

    def clickedCell_variety_table(self, row, col):
        if col != 2:
            return
        current_item = self.variety_table.item(row, col)
        if not current_item:
            return
        current_vid = self.variety_table.item(row, 0).id
        current_text = current_item.text()
        if current_text == "点击开启":
            is_active = 1
        else:
            is_active = 0
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'user/' + str(self.user_id) + '/variety/',
                headers={"Content-Type": "application/json;charset=utf8"},
                data=json.dumps({
                    "utoken": settings.app_dawn.value('AUTHORIZATION'),
                    "is_active": is_active,
                    "variety_id": current_vid,
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            current_item.setText("点击关闭" if is_active else "点击开启")


# 显示用户表格
class UsersTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(UsersTable, self).__init__(*args)
        self.setFocusPolicy(Qt.NoFocus)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def setRowContents(self, row_contents):
        self.clear()
        table_headers = ["序号", "用户名","手机", "加入时间", "最近登录", "邮箱","角色"]
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.setRowCount(len(row_contents))
        for row,row_item in enumerate(row_contents):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['username'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['phone'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row,2, item2)
            item3 = QTableWidgetItem(row_item['join_time'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['update_time'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['email'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)
            item6 = QTableWidgetItem(row_item["role_text"])
            item6.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 6, item6)

    def mousePressEvent(self, event):
        if event.buttons() != Qt.RightButton:
            return
        index = self.indexAt(QPoint(event.x(), event.y()))
        current_row = index.row()
        self.setCurrentIndex(index)
        if current_row < 0 :
            return
        menu = QMenu()
        variety_auth_action = menu.addAction("品种权限")
        variety_auth_action.triggered.connect(self.setUserVarietyAuth)
        role_modify_action = menu.addAction("角色设置")
        role_modify_action.triggered.connect(self.modifyUserRole)
        menu.exec_(QCursor.pos())
        super(UsersTable, self).mousePressEvent(event)

    def setUserVarietyAuth(self):
        current_row = self.currentRow()
        user_id = self.item(current_row, 0).id
        # 弹窗设置品种权限
        popup = VarietyAuthDialog(user_id=user_id)
        popup.get_varieties()
        popup.getCurrentUserAccessVariety()
        popup.exec_()

    def modifyUserRole(self):
        def commit():
            role_num = role_combobox.currentData()
            try:
                r = requests.patch(
                    url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/',
                    headers={"Content-Type": "application/json;charset=utf8"},
                    data=json.dumps({
                        'utoken': settings.app_dawn.value("AUTHORIZATION"),
                        'role_to': role_num
                    })
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(popup, '错误', '修改错误{}'.format(e))
            else:
                QMessageBox.information(popup, '成功', "修改用户角色成功")
                self.item(current_row, 6).setText(response['role_text'])
            finally:
                popup.close()
        current_row = self.currentRow()
        username = self.item(current_row, 1).text()
        user_id = self.item(current_row, 0).id
        role_text = self.item(current_row, 6).text()
        popup = QDialog(parent=self)
        popup.setFixedSize(250, 80)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        mainlayout = QVBoxLayout()
        layout = QHBoxLayout()
        popup.setWindowTitle("【"+ username+"】角色设置")
        layout.addStretch()
        layout.addWidget(QLabel("角色:", popup))
        role_combobox = QComboBox(popup)
        role_combobox.setFixedWidth(150)
        for role_item in [(1,"超级管理员"),(2,"运营管理员"),(3,"信息管理员"), (4,"研究员"),(5,"普通用户")]:
            role_combobox.addItem(role_item[1], role_item[0])
        role_combobox.setCurrentText(role_text)
        layout.addWidget(role_combobox)
        layout.addStretch()
        commit_button = QPushButton("确定")
        commit_button.clicked.connect(commit)
        mainlayout.addLayout(layout)
        mainlayout.addWidget(commit_button, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        popup.setLayout(mainlayout)
        popup.exec_()


# 用户管理页面
class UserManagePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(UserManagePage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        # 用户的类型选择与网络请求结果
        combo_message_layout = QHBoxLayout()
        self.role_combo = QComboBox()
        self.role_combo.activated.connect(self.getCurrentUsers)
        combo_message_layout.addWidget(self.role_combo)
        self.network_message = QLabel()
        combo_message_layout.addWidget(self.network_message)
        combo_message_layout.addStretch()
        layout.addLayout(combo_message_layout)
        # 用户表显示
        self.users_table = UsersTable()
        # self.users_table.network_result.connect(self.network_message.setText)
        layout.addWidget(self.users_table)
        self.setLayout(layout)
        self._addRoleComboItems()

    # 填充选择下拉框
    def _addRoleComboItems(self):
        for combo_item in [
            ('全部', 0),
            ('运营管理员', 2),  # 与后端对应
            ('信息管理员', 3),  # 与后端对应
            ('研究员', 4),  # 与后端对应
            ('普通用户', 5),
        ]:
            self.role_combo.addItem(combo_item[0], combo_item[1])

    # 获取相关用户
    def getCurrentUsers(self):
        current_data = self.role_combo.currentData()
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'users/?role_num='+str(current_data)+'&utoken=' + settings.app_dawn.value("AUTHORIZATION"),
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message.setText(str(e))
        else:
            self.network_message.setText(response['message'])
            self.users_table.setRowContents(response['users'])


"""功能管理"""


# 新增模块
class CreateNewModulePopup(QDialog):
    def __init__(self, module_combo, *args, **kwargs):
        super(CreateNewModulePopup, self).__init__(*args, **kwargs)
        self.setWindowTitle('新增模块')
        self.setMaximumSize(300,150)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:'), 0, 0)
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel(''), 1, 0)  # 占位
        # 附属
        layout.addWidget(QLabel('附属:'), 2, 0)
        self.attach_combo = QComboBox()
        # 添加选项
        self.attach_combo.addItem('无', None)
        for module_item in module_combo:
            self.attach_combo.addItem(module_item['name'], module_item['id'])
        layout.addWidget(self.attach_combo, 2, 1)
        layout.addWidget(QLabel(parent=self, objectName='nameError'), 3, 0, 1, 2)
        self.commit_button = QPushButton('确认提交', clicked=self.commit_new_module)
        layout.addWidget(self.commit_button, 4, 1)
        self.setLayout(layout)

    # 提交新增模块
    def commit_new_module(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入模块名称!')
            return
        parent = self.attach_combo.currentData()
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'module/',
                headers={'Content-Type': 'application/json;charset=utf8'},
                data=json.dumps({
                    'module_name': name,
                    'parent_id': parent,
                    'utoken': settings.app_dawn.value('AUTHORIZATION')
                })
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '失败', str(e))
        else:
            QMessageBox.information(self, '成功', '添加新功能模块成功!')
            self.close()


# 模块显示管理表格
class ModulesTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(ModulesTable, self).__init__(*args)
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.module_data = None

    # 设置表格数据
    def setRowContents(self, row_list):
        self.module_data = row_list
        self.clear()
        self.setRowCount(0)
        header_labels = ['序号', '名称', '排序']
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        current_row = 0
        for row, module_item in enumerate(self.module_data):
            self.insertRow(current_row)
            table_item0 = QTableWidgetItem(str(current_row + 1))
            table_item0.id = module_item['id']
            table_item0.setTextAlignment(Qt.AlignCenter)
            table_item0.setBackground(QBrush(QColor(218,233,231)))
            self.setItem(current_row, 0, table_item0)
            table_item1 = QTableWidgetItem(module_item['name'])
            table_item1.setTextAlignment(Qt.AlignCenter)
            table_item1.setBackground(QBrush(QColor(218,233,231)))
            self.setItem(current_row, 1, table_item1)
            current_row += 1
            for sub_module in module_item['subs']:
                self.insertRow(current_row)
                table_item0 = QTableWidgetItem(str(current_row + 1))
                table_item0.setTextAlignment(Qt.AlignCenter)
                table_item0.id = sub_module['id']
                self.setItem(current_row, 0, table_item0)
                table_item1 = QTableWidgetItem(sub_module['name'])
                table_item1.setTextAlignment(Qt.AlignCenter)
                self.setItem(current_row, 1, table_item1)
                current_row += 1


# 功能模块管理页面
class ModuleManagePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(ModuleManagePage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        # 信息显示与新增按钮布局
        message_button_layout = QHBoxLayout()
        self.network_message = QLabel()
        message_button_layout.addWidget(self.network_message)
        message_button_layout.addStretch()
        self.add_button = QPushButton('新增', clicked=self.create_new_module)
        message_button_layout.addWidget(self.add_button, alignment=Qt.AlignRight)
        # 模块编辑显示表格
        self.module_table = ModulesTable(parent=self)
        layout.addLayout(message_button_layout)
        layout.addWidget(self.module_table)
        self.setLayout(layout)

    # 获取系统模块信息
    def getCurrentModules(self):
        # 请求数据
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'module/?mc=' + settings.app_dawn.value('machine'),
                headers={"Content-Type":"application/json;charset=utf8"},
                data=json.dumps({
                    'utoken':settings.app_dawn.value('AUTHORIZATION')
                })

            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message.setText(str(e))
        else:
            self.network_message.setText(response['message'])
            self.module_table.setRowContents(response['modules'])

    # 新增系统模块
    def create_new_module(self):
        popup = CreateNewModulePopup(parent=self, module_combo=self.module_table.module_data)
        if not popup.exec_():
            self.getCurrentModules()


"""品种管理"""


# 弹窗新增品种主页
class CreateNewVarietyPopup(QDialog):
    def __init__(self, groups, *args, **kwargs):
        super(CreateNewVarietyPopup, self).__init__(*args, **kwargs)
        self.setFixedSize(300, 200)
        self.setWindowTitle("新增品种")
        layout = QGridLayout()
        layout.setParent(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # 填写名称
        layout.addWidget(QLabel('名称:',self), 0, 0)
        self.name_edit = QLineEdit(self)
        layout.addWidget(self.name_edit, 0, 1)
        # 填写英文代码
        layout.addWidget(QLabel('代码:',self), 1, 0)
        self.name_en_edit = QLineEdit(self)
        layout.addWidget(self.name_en_edit, 1, 1)
        # 选择分组
        layout.addWidget(QLabel('分组:', self), 2,0)
        self.group_combobox = QComboBox(self)
        for group_item in groups:
            self.group_combobox.addItem(group_item[1], group_item[0])
        layout.addWidget(self.group_combobox, 2, 1)
        # 交易所
        layout.addWidget(QLabel('交易所:', self), 3, 0)
        self.exchange_combobox = QComboBox(self)
        for exchange_item in [
            (1, "郑州商品交易所"), (2, '上海期货交易所'),
            (3, '大连商品交易所'), (4, '中国金融期货交易所'),
            (5, '上海国际能源交易中心')
        ]:
            self.exchange_combobox.addItem(exchange_item[1], exchange_item[0])
        layout.addWidget(self.exchange_combobox, 3,1)

        self.commit_button = QPushButton("提交", self)
        self.commit_button.clicked.connect(self.commit_new_variety)
        layout.addWidget(self.commit_button, 4, 0, 1, 2)
        self.setLayout(layout)

    # 新增品种
    def commit_new_variety(self):
        new_name = self.name_edit.text().strip()
        new_name_en = self.name_en_edit.text().strip()
        group_id = self.group_combobox.currentData()
        exchange = self.exchange_combobox.currentData()
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'variety/',
                headers={'Content-Type': 'application/json;charset=utf8'},
                data=json.dumps({
                    'variety_name': new_name,
                    "variety_name_en": new_name_en,
                    "parent_num": group_id,
                    "exchange_num": exchange,
                    "utoken": settings.app_dawn.value('AUTHORIZATION')
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", "新增品种错误!")
        else:
            QMessageBox.information(self, "成功", response['message'])
            self.close()


class VarietiesTable(QTableWidget):
    def __init__(self,*args, **kwargs):
        super(VarietiesTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def setRowContents(self, row_list):
        self.clear()
        self.setRowCount(0)
        header_labels = ['序号', '名称', '代码']
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        current_row = 0
        for row, variety_group in enumerate(row_list):
            self.insertRow(current_row)
            table_item0 = QTableWidgetItem(str(current_row + 1))
            table_item0.id = variety_group['id']
            table_item0.setTextAlignment(Qt.AlignCenter)
            table_item0.setBackground(QBrush(QColor(218, 233, 231)))
            self.setItem(current_row, 0, table_item0)
            table_item1 = QTableWidgetItem(variety_group['name'])
            table_item1.setTextAlignment(Qt.AlignCenter)
            table_item1.setBackground(QBrush(QColor(218, 233, 231)))
            self.setItem(current_row, 1, table_item1)
            table_item2 = QTableWidgetItem('')
            table_item2.setBackground(QBrush(QColor(218,233,231)))
            self.setItem(current_row, 2, table_item2)
            current_row += 1
            for sub_item in variety_group['subs']:
                self.insertRow(current_row)
                table_item0 = QTableWidgetItem(str(current_row + 1))
                table_item0.setTextAlignment(Qt.AlignCenter)
                table_item0.id = sub_item['id']
                self.setItem(current_row, 0, table_item0)
                table_item1 = QTableWidgetItem(sub_item['name'])
                table_item1.setTextAlignment(Qt.AlignCenter)
                self.setItem(current_row, 1, table_item1)
                table_item2 = QTableWidgetItem(sub_item['name_en'])
                table_item2.setTextAlignment(Qt.AlignCenter)
                self.setItem(current_row, 2, table_item2)
                current_row += 1

        return


# 品种管理页面
class VarietyManagePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietyManagePage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        combo_message_layout = QHBoxLayout()
        combo_message_layout.addStretch()
        # 新增品种按钮
        self.add_button = QPushButton('新增', parent=self, clicked=self.create_new_variety)
        combo_message_layout.addWidget(self.add_button)
        layout.addLayout(combo_message_layout)
        # 下方显示管理表格
        self.variety_table = VarietiesTable(parent=self)
        layout.addWidget(self.variety_table)
        self.setLayout(layout)
        self.all_varieties = []

    # 获取品种
    def getCurrentVarieties(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'variety/?way=group',
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.all_varieties = response['variety']
            self.variety_table.setRowContents(response['variety'])

    # 新增品种
    def create_new_variety(self):
        groups = [(group_item['id'], group_item['name']) for group_item in self.all_varieties]
        popup = CreateNewVarietyPopup(parent=self, groups=groups)
        popup.exec_()


"""广告管理"""


# 新增广告
class CreateAdvertisementPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateAdvertisementPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(350, 200)
        self.setWindowTitle("新建广告")
        layout = QGridLayout()
        layout.setParent(self)
        layout.addWidget(QLabel("标题:", self), 0, 0)
        self.title_edit = QLineEdit(self)
        layout.addWidget(self.title_edit, 0, 1)
        layout.addWidget(QLabel("图片:", self), 1, 0)
        self.image_path_edit = ImagePathLineEdit(self)
        layout.addWidget(self.image_path_edit, 1, 1)
        layout.addWidget(QLabel('文件:', self), 2, 0)
        self.file_path_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_path_edit, 2, 1)
        self.commit_button = QPushButton("提交", self)
        self.commit_button.clicked.connect(self.commit_new_advertisement)
        layout.addWidget(self.commit_button, 3, 0, 1, 2)
        self.setLayout(layout)

    def commit_new_advertisement(self):
        self.commit_button.setEnabled(False)
        # 获取上传的类型
        title = re.sub(r'\s+', '', self.title_edit.text())
        if not title:
            QMessageBox.information(self, "错误", "标题不能为空!")
            return
        if not all([self.file_path_edit.text(), self.image_path_edit.text()]):
            QMessageBox.information(self, "错误", "请设置广告图片和内容文件")
            return
        data = dict()
        data['ad_title'] = title  # 标题
        data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        image = open(self.image_path_edit.text(), 'rb')
        image_content = image.read()
        image.close()
        data['ad_image'] = ("ad_image.png", image_content)
        file = open(self.file_path_edit.text(), "rb")  # 获取文件
        file_content = file.read()
        file.close()
        # 文件内容字段
        data["ad_file"] = ("ad_file.pdf", file_content)
        encode_data = encode_multipart_formdata(data)
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'ad/',
                headers={
                    'Content-Type': encode_data[1]
                },
                data=encode_data[0]
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "失败", '上传新广告信息失败!')
        else:
            QMessageBox.information(self, "成功", '上传新广告信息成功!')
        finally:
            self.commit_button.setEnabled(True)
            self.close()


# 广告展示表格
class AdvertisementTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(AdvertisementTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.cellClicked.connect(self.cell_clicked)

    def cell_clicked(self, row, col):
        if col == 2:  # 查看图片
            item = self.item(row, col)
            image_url = item.image_url
            popup = QDialog(parent=self)
            popup.setFixedSize(660, 330)
            popup.setWindowTitle('图片')
            popup.setAttribute(Qt.WA_DeleteOnClose)
            layout = QVBoxLayout(popup)
            r = requests.get(url=settings.STATIC_PREFIX + image_url)
            image_label = QLabel(popup)
            image_label.setPixmap(QPixmap.fromImage(QImage.fromData(r.content)))
            image_label.setScaledContents(True)
            layout.addWidget(image_label)
            popup.setLayout(layout)
            popup.exec_()
        elif col == 3:  # 查看内容
            item = self.item(row, col)
            file_url = item.file_url
            popup = PDFContentPopup(title='广告内容', file=settings.STATIC_PREFIX + file_url)
            popup.exec_()
        else:
            pass

    def showRowContens(self, advertisement_list):
        self.clear()
        table_headers = ['序号', '创建日期','图片','内容']
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(advertisement_list):
            self.insertRow(row)
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem("查看")
            item2.image_url = row_item['image_url']
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem("查看")
            item3.file_url = row_item['file_url']
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)


# 广告设置
class AdvertisementPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(AdvertisementPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)
        # 信息展示与新增按钮
        layout.addWidget(QPushButton('新增', clicked=self.create_advertisement), alignment=Qt.AlignRight)
        # 当前数据显示表格
        self.advertisement_table = AdvertisementTable(self)
        layout.addWidget(self.advertisement_table)
        self.setLayout(layout)

    # 新增广告
    def create_advertisement(self):
        popup = CreateAdvertisementPopup(parent=self)
        popup.exec_()

    # 获取广告数据
    def getAdvertisements(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'ad/',
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            self.advertisement_table.showRowContens(response['adments'])


# 运营管理主页
class OperatorMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(OperatorMaintain, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0,0,0,1))
        layout.setSpacing(0)
        # 左侧管理项目列表
        self.operate_list = QListWidget(self)
        self.operate_list.setObjectName('optsList')
        self.operate_list.clicked.connect(self.operate_list_clicked)
        layout.addWidget(self.operate_list, alignment=Qt.AlignLeft)
        # 右侧tab显示
        self.frame_tab = QTabWidget()
        self.frame_tab.setDocumentMode(True)
        self.frame_tab.tabBar().hide()
        layout.addWidget(self.frame_tab)
        self.setLayout(layout)

        self.setStyleSheet("""
        #optsList{
            background-color: rgb(240,240,240);
            border:none;
            border-right: 1px solid rgb(180, 180, 180);
        }
        #optsList::item{
            height: 25px;
        }
        """)

    # 加入运营管理菜单
    def addOperatorItem(self):
        # u'运营数据', u'用户管理', u'客户端管理',
        self.operate_list.addItems([u'用户管理', u'功能管理', u'品种管理', u'广告管理'])

    # 点击左侧管理菜单
    def operate_list_clicked(self):
        text = self.operate_list.currentItem().text()
        # if text == u'运营数据':
        #     tab = OperateManagePage(parent=self)
        if text == u'用户管理':
            tab = UserManagePage(parent=self)
            tab.getCurrentUsers()
        elif text == u'功能管理':
            tab = ModuleManagePage(parent=self)
            tab.getCurrentModules()
        elif text == u'品种管理':
            tab = VarietyManagePage(parent=self)
            tab.getCurrentVarieties()
        elif text == u'广告管理':
            tab = AdvertisementPage(parent=self)
            tab.getAdvertisements()
        else:
            tab = QLabel(parent=self,
                         styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                         alignment=Qt.AlignCenter)
            tab.setText("「" + text + "」正在加紧开放中...")
        self.frame_tab.clear()
        self.frame_tab.addTab(tab, text)