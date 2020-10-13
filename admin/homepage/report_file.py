# _*_ coding:utf-8 _*_
# @File  : report_file.py
# @Time  : 2020-09-29 15:58
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, QFile
from popup.message import InformationPopup
from utils.client import get_user_token
from utils.multipart import generate_multipart_data
from settings import SERVER_API, logger, STATIC_URL
from widgets.pdf_shower import PDFContentPopup
from .report_file_ui import ReportFileAdminUI


class ReportFileAdmin(ReportFileAdminUI):
    def __init__(self, *args, **kwargs):
        super(ReportFileAdmin, self).__init__(*args, **kwargs)
        self.selected_file_path = None  # 选择的文件
        self.local_file_path = None     # 本地文件路径
        self.selected_varieties = list()  # 选择的关联品种
        self.selected_varieties_zh = list()  # 关联品种的中文
        # 添加报告类型
        for type_item in [
            {"name": "日报", "type": "daily"},
            {"name": "周报", "type": "weekly"},
        ]:
            self.report_type.addItem(type_item["name"], type_item["type"])
            self.manager_report_type.addItem(type_item["name"], type_item["type"])

        self._get_user_variety()  # 获取有权限的品种

        # 获取服务端当前的所有文件
        self._get_files_in_server()

        # 监测本地文件选择框
        self.local_file_edit.textChanged.connect(self.selected_local_file)
        # 选择品种
        self.variety_combobox.activated.connect(self.selected_relative_variety)
        # 清除品种
        self.clear_relative_button.clicked.connect(self.clear_relative_variety)
        # 表格操作
        self.file_table.cellClicked.connect(self.file_table_operation)
        # 创建报告
        self.confirm_button.clicked.connect(self.create_report_file)

        # 管理报告查询
        self.manager_query_button.clicked.connect(self.query_reports)
        # 管理表格的点击事件
        self.manager_table.cellClicked.connect(self.clicked_manager_report)

    def selected_relative_variety(self):
        """ 选择关联的品种 """
        if self.selected_file_path or self.local_file_path:
            variety_en = self.variety_combobox.currentData()
            if variety_en not in self.selected_varieties:
                self.selected_varieties.append(variety_en)
            variety_text = self.variety_combobox.currentText()
            if variety_text not in self.selected_varieties_zh:
                self.selected_varieties_zh.append(variety_text)
            self.relative_variety.setText(";".join(self.selected_varieties_zh))
            self.has_relative_variety()
        else:
            self.clear_relative_variety()
            self.relative_variety.setText("请选择文件再选择品种")

    def clear_relative_variety(self):
        """ 清除关联品种 """
        self.selected_varieties.clear()
        self.selected_varieties_zh.clear()
        self.relative_variety.setText("下拉框选择品种(多选)")
        self.no_relative_variety()

    def selected_local_file(self, text):
        """ 选择本地文件 """
        if text:  # 选择了文件路径
            self.local_file_path = text
            self.filename.setText("从表格选择文件")
            self.no_selected_file()
            self.selected_file_path = None
        else:  # 空文件
            self.local_file_path = None
        self.clear_relative_variety()  # 只要文件变化了就清除关联品种

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
            self.manager_variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])

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
        self.file_table.clearContents()
        self.file_table.setRowCount(len(files_list))
        for row, row_item in enumerate(files_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setData(Qt.UserRole, row_item["relative_path"])
            self.file_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["filename"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["file_size"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["create_time"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem("查看")
            item4.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 4, item4)

            item5 = QTableWidgetItem("选择")
            item5.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 5, item5)

            item6 = QTableWidgetItem("删除")
            item6.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 6, item6)

    def file_table_operation(self, row, col):
        """ 表格操作 """
        current_file_path = self.file_table.item(row, 0).data(Qt.UserRole)
        if col == 4:  # 查看
            filename = self.file_table.item(row, 1).text()
            url = SERVER_API + "wechat-files/{}".format(current_file_path)
            p = PDFContentPopup(title=filename, file=url)
            p.exec_()
        elif col == 5:  # 选择
            if self.local_file_path is not None:
                p = InformationPopup("您已选择本地文件,无法再选择网络文件。\n如需取消本地文件,请点击选框后直接取消。", self)
                p.exec_()
                return
            filename = self.file_table.item(row, 1).text()
            self.filename.setText(filename)
            self.selected_file_path = current_file_path
            self.has_selected_file()
        elif col == 6:  # 删除
            self.delete_wechat_file(row, current_file_path)
        else:
            pass

    def create_report_file(self):
        """ 从网络文件创建报告 """
        # 验证是否能发送请求
        if not self.selected_varieties:
            p = InformationPopup("未选择关联品种", self)
            p.exec_()
            return
        # 公共body_data
        body_data = {
            "date": self.date_edit.text(),
            "relative_varieties": ";".join(self.selected_varieties),
            "report_type": self.report_type.currentData(),
            "rename_text": self.rename_edit.text().strip()
        }
        if self.local_file_path:  # 上传本地文件
            self.send_local_report(body_data)
        elif self.selected_file_path:  # 选择网络文件
            self.send_network_report(body_data.copy())
        else:
            p = InformationPopup("未选择相关报告文件", self)
            p.exec_()

    def send_local_report(self, body_data):
        """ 上传本地报告文件 """

        def create_report_reply():
            if reply.error():
                message = "创建报告失败!"
            else:
                message = "创建报告成功!"
                self.local_file_edit.clear()
                self.clear_relative_variety()
            reply.deleteLater()
            p = InformationPopup(message, self)
            p.exec_()
        # 文件信息
        file = QFile(self.local_file_path)
        file.open(QFile.ReadOnly)
        file_dict = {"report_file": file}
        # 其他信息
        text_dict = body_data.copy()
        multipart_data = generate_multipart_data(text_dict, file_dict)
        url = SERVER_API + 'report-file/'
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, multipart_data)
        reply.finished.connect(create_report_reply)
        multipart_data.setParent(reply)

    def send_network_report(self, body_data):
        """ 使用网络文件创建 """
        def create_report_reply():
            if reply.error():
                message = "创建报告失败!"
            else:
                message = "创建报告成功!"
                self.file_table.removeRow(self.file_table.currentRow())
                self.clear_relative_variety()
            reply.deleteLater()
            p = InformationPopup(message, self)
            p.exec_()

        url = SERVER_API + "wechat-files/{}".format(self.selected_file_path)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(create_report_reply)

    def delete_wechat_file(self, current_row, relative_path):
        """ 删除网络保存的文件 """

        def delete_wechat_file_reply():
            """ 删除网络保存的文件返回 """
            if reply.error():
                p = InformationPopup("删除失败!", self)
                p.exec_()
            else:
                p = InformationPopup("删除成功!", self)
                p.exec_()
                self.file_table.removeRow(current_row)
            reply.deleteLater()

        url = SERVER_API + "wechat-files/{}".format(relative_path)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.deleteResource(request)
        reply.finished.connect(delete_wechat_file_reply)

    def query_reports(self):
        """ 查询当前条件下的报告 """
        variety_en = self.manager_variety_combobox.currentData()
        report_type = self.manager_report_type.currentData()
        current_date = self.manager_date.text()
        # 进行查询
        url = SERVER_API + "report-file/?query_date={}&report_type={}&variety_en={}".format(current_date, report_type, variety_en)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.query_report_reply)

    def query_report_reply(self):
        """ 查询报告返回 """
        reply = self.sender()
        if reply.error():
            report_list = list()
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            report_list = data["reports"]
        self.fill_manager_table(report_list)
        reply.deleteLater()

    def fill_manager_table(self, reports):
        """ 填充管理报告的表格 """
        self.manager_table.clearContents()
        self.manager_table.setRowCount(len(reports))
        for row, row_item in enumerate(reports):
            item0 = QTableWidgetItem(row_item["date"])
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setData(Qt.UserRole, row_item["id"])
            self.manager_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["variety_en"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.manager_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["type_text"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.manager_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["filename"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.manager_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem("查看")
            item4.setTextAlignment(Qt.AlignCenter)
            item4.setData(Qt.UserRole, row_item["filepath"])
            self.manager_table.setItem(row, 4, item4)

            if row_item["is_active"]:
                item5 = QTableWidgetItem("是")
            else:
                item5 = QTableWidgetItem("否")
            item5.setTextAlignment(Qt.AlignCenter)
            self.manager_table.setItem(row, 5, item5)

            item6 = QTableWidgetItem("删除")
            item6.setTextAlignment(Qt.AlignCenter)
            self.manager_table.setItem(row, 6, item6)

    def clicked_manager_report(self, row, col):
        """ 点击管理报告 """
        report_id = self.manager_table.item(row, 0).data(Qt.UserRole)
        if col == 5:  # 改变是否公开
            self.change_report_opened(row, report_id)
        elif col == 6:  # 删除报告
            self.delete_report(row, report_id)
        elif col == 4:  # 查看
            filepath = self.manager_table.item(row, col).data(Qt.UserRole)
            filename = self.manager_table.item(row, 3).text()
            url = STATIC_URL + filepath
            p = PDFContentPopup(title=filename, file=url)
            p.exec_()
        else:
            pass

    def change_report_opened(self, current_row, report_id):
        """ 改变报告是否公开的情况 """
        def change_report_reply():
            if reply.error():
                p = InformationPopup("修改失败", self)
            else:
                p = InformationPopup("修改成功", self)
                text = "否" if self.manager_table.item(current_row, 5).text() == "是" else "是"
                self.manager_table.item(current_row, 5).setText(text)
            p.exec_()
            reply.deleteLater()

        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "report-file/{}/".format(report_id)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        reply = network_manager.put(request, None)
        reply.finished.connect(change_report_reply)

    def delete_report(self, current_row, report_id):
        """ 删除一条报告 """

        def delete_report_reply():
            if reply.error():
                p = InformationPopup("删除失败", self)
            else:
                p = InformationPopup("删除成功", self)
                self.manager_table.removeRow(current_row)
            p.exec_()
            reply.deleteLater()

        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "report-file/{}/".format(report_id)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        reply = network_manager.deleteResource(request)
        reply.finished.connect(delete_report_reply)

