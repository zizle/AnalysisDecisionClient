# _*_ coding:utf-8 _*_
# @File  : user_data.py
# @Time  : 2020-09-03 14:12
# @Author: zizle
import os
import json
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import qApp, QListWidgetItem, QTableWidgetItem, QPushButton
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from settings import SERVER_API, logger, BASE_DIR
from utils.client import get_user_token, get_client_uuid
from popup.industry_popup import UpdateFolderPopup
from .user_data_ui import UserDataMaintainUI, SheetChartUI


class UserDataMaintain(UserDataMaintainUI):
    def __init__(self, *args, **kwargs):
        super(UserDataMaintain, self).__init__(*args, **kwargs)
        self.is_ready = False  # 左侧菜单选择时是否请求品种下的数据组

        for menu_item in [
            {"name": "数据源配置", "name_en": "source_config"},
            {"name": "品种数据表", "name_en": "variety_sheet"},
            {"name": "我的数据图", "name_en": "sheet_chart"},
        ]:
            menu = QListWidgetItem(menu_item["name"])
            menu.setData(Qt.UserRole, menu_item["name_en"])
            self.maintain_menu.addItem(menu)

        self.maintain_menu.clicked.connect(self.selected_maintain_menu)   # 选择操作菜单
        self.source_config_widget.confirm_group_button.clicked.connect(self.create_new_sheet_group)  # 确定新增分组
        # 数据源配置页品种选择变化信号连接(请求当前品种下的分组)
        self.source_config_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        # 数据表显示页品种选择变化信号连接放在请求完品种权限返回添加完数据之后(不在__init__内连接信号可以减少一次请求分组的网络)

        self._get_user_variety()  # 获取用户有权限的品种(置于信号连接之后确保首次信号执行)

        self.source_config_widget.new_config_button.clicked.connect(self.config_update_folder)  # 调整配置更新文件夹
        self.source_config_widget.group_combobox.currentTextChanged.connect(self.show_groups_folder_list)  # 显示品种组的更新文件夹

    def _get_user_variety(self):
        """ 获取用户有权限的品种信息 """
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/variety-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_variety_reply)

    def user_variety_reply(self):
        """ 获取用户的品种权限返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            pass
        else:
            data = json.loads(data.decode("utf-8"))
            current_user = data.get("user")
            if not current_user:
                logger.error("登录过期了,用户获取有权限的品种失败!")
                return
            self._combobox_allow_varieties(data["varieties"])
        reply.deleteLater()

    def _combobox_allow_varieties(self, varieties):
        today_str = datetime.today().strftime("%Y-%m-%d")
        for variety_item in varieties:
            if not variety_item["expire_date"] or variety_item["expire_date"] <= today_str:
                continue
            # 数据源配置页
            self.source_config_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 数据表显示页
            self.variety_sheet_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 品种图形显示页
            self.sheet_chart_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])

        # 数据表显示页品种选择变化(不在__init__内连接信号可以减少一次网络请求)
        self.variety_sheet_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        self.is_ready = True

    def selected_maintain_menu(self):
        """ 选择了左侧菜单 """
        current_menu = self.maintain_menu.currentItem().data(Qt.UserRole)
        if current_menu == "source_config":
            self.maintain_frame.setCurrentIndex(0)
        elif current_menu == "variety_sheet":
            self.maintain_frame.setCurrentIndex(1)
        elif current_menu == "sheet_chart":
            self.maintain_frame.setCurrentIndex(2)
            return   # 图形界面无需再请求品种下的数据分组
        else:
            return
        if self.is_ready:
            self.variety_combobox_changed()  # 手动调用请求品种下的分组(否则第一次切换到品种表页面没有分组)

    def config_update_folder(self):
        """ 调整配置更新的文件夹 """
        variety_text, variety_en = self.source_config_widget.variety_combobox.currentText(), self.source_config_widget.variety_combobox.currentData()
        group_text, group_id = self.source_config_widget.group_combobox.currentText(), self.source_config_widget.group_combobox.currentData()
        if not all([variety_text, variety_en, group_text, group_id]):
            self.source_config_widget.tips_message.setText("选择正确的品种分组再配置.")
            return
        self.source_config_widget.tips_message.setText("")
        popup = UpdateFolderPopup(variety_text=variety_text, variety_en=variety_en, group_text=group_text, group_id=group_id, parent=self)
        popup.successful_signal.connect(self.config_folder_successfully)
        popup.exec_()

    def config_folder_successfully(self, text):
        """ 调整文件夹配置成功 """
        self.source_config_widget.tips_message.setText(text)
        self.sender().close()
        # 刷新
        self.show_groups_folder_list()

    def show_groups_folder_list(self):
        variety_en, variety_text = self.source_config_widget.variety_combobox.currentData(), self.source_config_widget.variety_combobox.currentText()
        group_id = self.source_config_widget.group_combobox.currentData()
        client = get_client_uuid()
        db_path = os.path.join(BASE_DIR, "dawn/local_data.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if group_id == 0:
            cursor.execute(
                "SELECT ID,VARIETY_EN,GROUP_ID,FOLDER FROM UPDATE_FOLDER WHERE VARIETY_EN=? AND CLIENT=?;",
                (variety_en, client)
            )
        else:
            cursor.execute(
                "SELECT ID,VARIETY_EN,GROUP_ID,FOLDER FROM UPDATE_FOLDER WHERE VARIETY_EN=? AND GROUP_ID=? AND CLIENT=?;",
                (variety_en, group_id, client)
            )
        folder_list = cursor.fetchall()
        cursor.close()
        conn.close()
        group_dict = dict()
        for i in range(self.source_config_widget.group_combobox.count()):
            group_dict[self.source_config_widget.group_combobox.itemData(i)] = self.source_config_widget.group_combobox.itemText(i)
        self.source_config_widget.config_table.clearContents()
        self.source_config_widget.config_table.setRowCount(len(folder_list))
        for row, row_item in enumerate(folder_list):
            item0 = QTableWidgetItem(str(row_item[0]))
            item0.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(variety_text)
            item1.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 1, item1)

            text2 = group_dict.get(row_item[2], '')
            item2 = QTableWidgetItem(text2)
            item2.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item[3])
            item3.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 3, item3)

            item4_button = QPushButton("点击更新", self.source_config_widget.config_table)
            setattr(item4_button, "row_index", row)
            item4_button.clicked.connect(self.updating_sheets_of_folder)
            self.source_config_widget.config_table.setCellWidget(row, 4, item4_button)

    def updating_sheets_of_folder(self):
        """ 更新文件夹内的所有数据表 """
        if self.source_config_widget.is_updating:
            self.source_config_widget.tips_message.setText("当前有数据正在更新,完成后再进行操作! ")
            return
        button_clicked = self.sender()
        current_row = getattr(button_clicked, "row_index")
        variety_en = self.source_config_widget.variety_combobox.currentData()
        group_text = self.source_config_widget.config_table.item(current_row, 2).text()
        folder_path = self.source_config_widget.config_table.item(current_row, 3).text()
        group_id = None
        for i in range(self.source_config_widget.group_combobox.count()):
            if self.source_config_widget.group_combobox.itemText(i) == group_text:
                group_id = self.source_config_widget.group_combobox.itemData(i)
        if not group_id:
            self.source_config_widget.tips_message.setText("数据组别错误,无法更新数据!")
            return
        # 关闭按钮的点击事件
        button_clicked.setEnabled(False)
        # 开启数据更新的文字提示
        self.source_config_widget.tips_message.setText("正在更新数据,请稍候 ")
        self.source_config_widget.updating_timer.start(400)
        self.source_config_widget.is_updating = True
        print(variety_en, group_id, folder_path)

    def update_folder_sheets_to_server(self, folder_path):
        """ 读取数据,更新数据到服务端 """


    def variety_combobox_changed(self):
        """ 界面品种变化 """
        current_widget = self.maintain_frame.currentWidget()
        current_variety = current_widget.variety_combobox.currentData()
        if isinstance(current_widget, SheetChartUI):
            return
        self.get_variety_sheet_group(current_variety)

    def create_new_sheet_group(self):
        """ 创建新的品种数据分组 """
        group_name = self.source_config_widget.new_group_edit.text().strip()

        current_variety = self.source_config_widget.variety_combobox.currentData()
        if not all([group_name, current_variety]):
            return
        user_token = get_user_token()
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, json.dumps({"group_name": group_name}).encode("utf-8"))
        reply.finished.connect(self.variety_sheet_group_reply)

    def get_variety_sheet_group(self, current_variety):
        """ 获取品种下的数据分组 """
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(request)
        reply.finished.connect(self.variety_sheet_group_reply)

    def variety_sheet_group_reply(self):
        """ 品种下的数据分组返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            logger.error("用户(新建时)获取数据分组失败:{}".format(data))
        else:
            self.source_config_widget.hide_create_new_group()
            current_widget = self.maintain_frame.currentWidget()
            data = json.loads(data.decode("utf-8"))
            current_widget.group_combobox.clear()
            current_widget.group_combobox.addItem("全部", 0)
            for group_item in data["groups"]:
                current_widget.group_combobox.addItem(group_item["group_name"], group_item["id"])
        reply.deleteLater()
        # 再次调用数据源配置页的查询已配置的文件夹内容项(由于变化了就连接信号,获取组不全需手动再次调用)
        self.show_groups_folder_list()

