# _*_ coding:utf-8 _*_
# @File  : report_file.py
# @Time  : 2020-09-29 15:58
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl
from utils.client import get_user_token
from settings import SERVER_API, logger
from .report_file_ui import ReportFileAdminUI


class ReportFileAdmin(ReportFileAdminUI):
    def __init__(self, *args, **kwargs):
        super(ReportFileAdmin, self).__init__(*args, **kwargs)

        # 添加报告类型
        for type_item in [
            {"name": "日报", "type": "daily"},
            {"name": "周报", "type": "weekly"},
        ]:
            self.report_type.addItem(type_item["name"], type_item["type"])

        self._get_user_variety()  # 获取有权限的品种

        # 获取服务端当前的所有文件
        self._get_files_in_server()

    def _get_user_variety(self):
        """ 获取用户有权限的品种 """
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
        """ 填充选项 """
        for variety_item in varieties:
            self.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])

    def _get_files_in_server(self):
        """ 获取服务端当前有的pdf文件 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "wechat-files/"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.wechat_files_reply)

    def wechat_files_reply(self):
        reply = self.sender()
        if reply.error():
            file_list = list()
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            file_list = data["file_list"]
        reply.deleteLater()
        self.table_show_files(file_list)

    def table_show_files(self, files_list):
        """ 文件信息在表格显示 """
        print(files_list)
        self.file_table.clearContents()
        self.file_table.setRowCount(len(files_list))
        for row, row_item in enumerate(files_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["filename"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem()
            item2.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 2, item2)







