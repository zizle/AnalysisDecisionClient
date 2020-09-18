# _*_ coding:utf-8 _*_
# @File  : user_extension.py
# @Time  : 2020-09-16 13:35
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QPushButton
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl
from settings import SERVER_API, logger
from .user_extension_ui import UserExtensionUI


class UserExtensionPage(UserExtensionUI):
    def __init__(self, *args, **kwargs):
        super(UserExtensionPage, self).__init__(*args, **kwargs)
        # 类型
        self.user_type_combobox.addItem("内部用户", "inner")
        self.user_type_combobox.addItem("普通用户", "normal")
        # 查询
        self.query_button.clicked.connect(self.query_target_users)

    def query_target_users(self):
        """ 查询用户 """
        user_type = self.user_type_combobox.currentData()
        phone = self.phone_edit.text().strip()
        url = SERVER_API + "user/extension/?user_type={}&phone={}".format(user_type, phone)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.get_user_extension_reply)

    def get_user_extension_reply(self):
        """ 获取用户的拓展信息返回 """
        reply = self.sender()
        if reply.error():
            logger.error("获取用户的拓展信息失败:{}".format(reply.error()))
        else:
            data = json.loads(reply.readAll().data().decode('utf-8'))
            users = data.get("users", [])
            self.show_users_in_table(users)
        reply.deleteLater()

    def show_users_in_table(self, users_list):
        print(users_list)
        self.user_table.clearContents()
        self.user_table.setRowCount(len(users_list))
        for row, row_item in enumerate(users_list):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            self.user_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["phone"])
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(Qt.ItemIsEditable)
            self.user_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["wx_id"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 2, item2)

            item3_button = QPushButton("确定", self)
            setattr(item3_button, "row_index", row)
            self.user_table.setCellWidget(row, 3, item3_button)
            item3_button.clicked.connect(self.modify_user_extension)

    def modify_user_extension(self):
        """ 修改用户的拓展信息 """
        sender_button = self.sender()
        current_row = getattr(sender_button, "row_index")
        user_id = self.user_table.item(current_row, 0).text()
        wx_id = self.user_table.item(current_row, 2).text()
        # 请求修改
        body_data = {"user_id": user_id, "wx_id": wx_id}
        url = SERVER_API + "user/extension/{}/".format(user_id)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.put(QNetworkRequest(QUrl(url)), json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.modify_user_extension_reply)

    def modify_user_extension_reply(self):
        """ 用户修改信息返回 """
        reply = self.sender()
        if reply.error():
            self.message_label.setText("修改信息失败!")
        else:
            self.message_label.setText("修改信息成功!")




