# _*_ coding:utf-8 _*_
# @File  : client_manager.py
# @Time  : 2020-09-10 17:48
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QPushButton
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QBrush, QColor
from settings import SERVER_API, logger
from utils.client import get_user_token
from .client_manager_ui import ClientManageUI


class ClientManage(ClientManageUI):
    def __init__(self, *args, **kwargs):
        super(ClientManage, self).__init__(*args, **kwargs)
        self.query_button.clicked.connect(self._get_current_clients)

        self.uuid_edit.textChanged.connect(self._get_client_with_uuid)

    def _get_current_clients(self):
        """ 获取当前条件下的client """
        is_manager = self.type_combobox.currentData()
        client_type = "manager" if is_manager else "normal"
        url = SERVER_API + "client/?c_type={}".format(client_type)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.get_clients_reply)

    def _get_client_with_uuid(self):
        """ 根据uuid获取客户端 """
        client_uuid = self.uuid_edit.text().strip()
        if len(client_uuid) != 36:
            self.client_table.clearContents()
            self.client_table.setRowCount(0)
            return
        url = SERVER_API + "client/{}/".format(client_uuid)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.get_clients_reply)

    def get_clients_reply(self):
        """ 获取客户端返回 """
        reply = self.sender()
        if reply.error():
            logger.error("获取客户端列表失败了:{}".format(reply.error()))
            return
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            self.show_clients_in_table(data["clients"])
        reply.deleteLater()

    def show_clients_in_table(self, clients):
        """ 表格显示所有客户端列表 """
        self.client_table.clearContents()
        self.client_table.setRowCount(len(clients))
        for row, row_item in enumerate(clients):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            item0.setForeground(QBrush(QColor(66, 66, 66)))
            self.client_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["join_date"])
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(Qt.ItemIsEditable)
            item1.setForeground(QBrush(QColor(66, 66, 66)))
            self.client_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["client_name"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.client_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["machine_uuid"])
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setFlags(Qt.ItemIsEditable)
            item3.setForeground(QBrush(QColor(66, 66, 66)))
            self.client_table.setItem(row, 3, item3)

            text, check, f_color = ("管理端", Qt.Checked, QColor(66, 233, 66)) if row_item["is_manager"] else (
                "客户端", Qt.Unchecked, QColor(233, 66, 66))
            item4 = QTableWidgetItem(text)
            item4.setTextAlignment(Qt.AlignCenter)
            item4.setCheckState(check)
            item4.setForeground(QBrush(f_color))
            self.client_table.setItem(row, 4, item4)

            text, check, f_color = ("启用", Qt.Checked, QColor(66, 233, 66)) if row_item["is_active"] else (
                "禁用", Qt.Unchecked, QColor(233, 66, 66))
            item5 = QTableWidgetItem(text)
            item5.setTextAlignment(Qt.AlignCenter)
            item5.setCheckState(check)
            item5.setForeground(QBrush(f_color))
            self.client_table.setItem(row, 5, item5)

            item6_button = QPushButton("确定", self)
            setattr(item6_button, "row_index", row)
            item6_button.clicked.connect(self.modify_client_information)
            self.client_table.setCellWidget(row, 6, item6_button)

    def modify_client_information(self):
        """ 修改客户端的基本信息 """
        sender_button = self.sender()
        current_row = getattr(sender_button, "row_index")
        client_id = self.client_table.item(current_row, 0).text()
        client_name = self.client_table.item(current_row, 2).text().strip()
        client_uuid = self.client_table.item(current_row, 3).text()
        is_manager = 1 if self.client_table.item(current_row, 4).checkState() else 0
        is_active = 1 if self.client_table.item(current_row, 5).checkState() else 0
        body_data = {
            "client_id": client_id,
            "client_name": client_name,
            "is_manager": is_manager,
            "is_active": is_active,
            "client_uuid": client_uuid
        }
        url = SERVER_API + 'client/{}/'.format(client_id)
        request = QNetworkRequest(QUrl(url))
        user_token = get_user_token()
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        network_manger = getattr(qApp, "_network")
        reply = network_manger.put(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.modify_client_reply)

    def modify_client_reply(self):
        """ 修改客户端信息返回 """
        reply = self.sender()
        if reply.error():
            self.network_message.setText("修改客户端信息错误:{}".format(reply.error()))
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.network_message.setText(data["message"])
        reply.deleteLater()
