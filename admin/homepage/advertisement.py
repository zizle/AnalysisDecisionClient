# _*_ coding:utf-8 _*_
# @File  : advertisement.py
# @Time  : 2020-10-12 15:50
# @Author: zizle
import json
from PyQt5.QtCore import QFile, QUrl, Qt
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtGui import QColor, QBrush
from utils.multipart import generate_multipart_data
from utils.client import get_user_token
from popup.message import InformationPopup
from popup.advertisement import ImagePopup, TextPopup
from widgets.pdf_shower import PDFContentPopup
from settings import SERVER_API, STATIC_URL
from .advertisement_ui import HomepageAdAdminUI


class HomepageAdAdmin(HomepageAdAdminUI):
    AD_TYPE = {
        "file": "文件显示",
        "web": "跳转网址",
        "content": "直显内容"
    }

    def __init__(self, *args, **kwargs):
        super(HomepageAdAdmin, self).__init__(*args, **kwargs)
        # 添加类型选择
        for key, value in self.AD_TYPE.items():
            self.ad_type.addItem(value, key)
        self.change_edit_widgets(ad_type="file")
        # 类型变化
        self.ad_type.currentIndexChanged.connect(self.select_ad_type_changed)
        # 确认创建
        self.create_button.clicked.connect(self.create_new_advertisement)
        # 初始获取所有广告信息
        self.read_all_advertisements()
        # 广告管理表格的点击事件
        self.ad_table.cellClicked.connect(self.manager_advertisement)

    def read_all_advertisements(self):
        """ 读取系统中存在的所有的广告信息 """
        url = SERVER_API + 'advertisement/?is_active=0'
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.read_advertisement_reply)

    def read_advertisement_reply(self):
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_all_advertisement(data["advertisements"])
        reply.deleteLater()

    def show_all_advertisement(self, advertisements):
        """ 显示系统中所有广告信息供管理 """
        self.ad_table.clearContents()
        self.ad_table.setRowCount(len(advertisements))
        for row, ad_item in enumerate(advertisements):
            item0 = QTableWidgetItem(str(ad_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            self.ad_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(ad_item["title"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.ad_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(self.AD_TYPE.get(ad_item["ad_type"], '未知'))
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setData(Qt.UserRole, ad_item["ad_type"])
            self.ad_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem("查看图片")
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setData(Qt.UserRole, ad_item["image"])
            self.ad_table.setItem(row, 3, item3)
            item4 = QTableWidgetItem("查看文件")
            item4.setData(Qt.UserRole, ad_item["filepath"])
            item4.setTextAlignment(Qt.AlignCenter)
            self.ad_table.setItem(row, 4, item4)
            item5 = QTableWidgetItem("查看网址")
            item5.setTextAlignment(Qt.AlignCenter)
            item5.setData(Qt.UserRole, ad_item["web_url"])
            self.ad_table.setItem(row, 5, item5)
            item6 = QTableWidgetItem("查看内容")
            item6.setTextAlignment(Qt.AlignCenter)
            item6.setData(Qt.UserRole, ad_item["content"])
            self.ad_table.setItem(row, 6, item6)
            item7 = QTableWidgetItem("备注")
            item7.setForeground(QBrush(QColor(66, 66, 233)))
            item7.setData(Qt.UserRole, ad_item["note"])
            item7.setTextAlignment(Qt.AlignCenter)
            self.ad_table.setItem(row, 7, item7)

            text, q_color = ("启用", QColor(66, 233, 66)) if ad_item["is_active"] else ("未启用", QColor(233, 66, 66))
            item8 = QTableWidgetItem(text)
            item8.setForeground(QBrush(q_color))
            item8.setTextAlignment(Qt.AlignCenter)
            self.ad_table.setItem(row, 8, item8)

    def manager_advertisement(self, row, col):
        """ 管理广告 """
        advertisement_id = self.ad_table.item(row, 0).text()
        advertisement_type = self.ad_table.item(row, 2).data(Qt.UserRole)
        if col == 3:  # 查看图片
            image_url = self.ad_table.item(row, col).data(Qt.UserRole)
            p = ImagePopup(STATIC_URL + image_url, self)
            p.setWindowTitle("广告图片")
            p.exec_()
        elif col == 4:  # 查看文件
            if advertisement_type != "file":
                p = InformationPopup("此广告类型非文件显示", self)
                p.exec_()
                return
            file_url = STATIC_URL + self.ad_table.item(row, col).data(Qt.UserRole)
            p = PDFContentPopup(file=file_url, title="广告文件")
            p.exec_()
        elif col in [5, 6, 7]:  # 5查看网址,6查看内容,7查看备注
            titles = [None, None, None, None, None, "查看网址", "查看内容", "查看备注"]
            message = self.ad_table.item(row, col).data(Qt.UserRole)
            p = TextPopup(message, self)
            p.setWindowTitle(titles[col])
            p.exec_()
        elif col == 8:  # 设置启用与不启用
            self.change_advertisement_active(advertisement_id)

    def change_advertisement_active(self, ad_id):
        url = SERVER_API + 'advertisement/{}/'.format(ad_id)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.put(QNetworkRequest(QUrl(url)), None)
        reply.finished.connect(self.modify_advertisement_reply)

    def modify_advertisement_reply(self):
        """ 修改广告启用返回 """
        reply = self.sender()
        if reply.error():
            p = InformationPopup("修改启用失败", self)
            p.exec_()
        else:
            p = InformationPopup("修改启用成功", self)
            p.exec_()
            self.read_all_advertisements()
        reply.deleteLater()

    def select_ad_type_changed(self):
        """ 选择广告的类型改变了 """
        current_type = self.ad_type.currentData()
        self.change_edit_widgets(current_type)

    def change_edit_widgets(self, ad_type):
        """ 改变创建的类型 """
        if ad_type == "file":
            self.file_label.show()
            self.filepath_edit.show()
            # 隐藏其他控件
            self.web_label.hide()
            self.web_edit.hide()
            self.web_edit.clear()
            self.content_label.hide()
            self.content_edit.hide()
            self.content_edit.clear()
        elif ad_type == "web":
            self.web_label.show()
            self.web_edit.show()
            self.file_label.hide()
            self.filepath_edit.hide()
            self.filepath_edit.clear()
            self.content_label.hide()
            self.content_edit.hide()
            self.content_edit.clear()
        elif ad_type == "content":
            self.content_label.show()
            self.content_edit.show()
            self.file_label.hide()
            self.filepath_edit.hide()
            self.filepath_edit.clear()
            self.web_label.hide()
            self.web_edit.hide()
            self.web_edit.clear()
        else:
            pass

    def get_new_advertisement_params(self):
        """ 获取新广告的参数 """
        current_type = self.ad_type.currentData()
        params = {
            "title": self.new_title.text().strip(),
            "ad_type": current_type,
            "image": self.imagepath_edit.text(),
            "filepath": '',
            "web_url": '',
            "content": '',
            "note": '',
        }
        if current_type == "file":
            params["filepath"] = self.filepath_edit.text()
        elif current_type == "web":
            params["web_url"] = self.web_edit.text().strip()
        elif current_type == "content":
            params["content"] = self.content_edit.text().strip()
        else:
            pass
        return params

    def create_new_advertisement(self):
        """ 确认创建新的广告 """
        ad_params = self.get_new_advertisement_params()
        if not all([ad_params["image"], ad_params["title"]]):
            p = InformationPopup("标题和图片不能为空!", self)
            p.exec_()
            return
        self.create_button.setEnabled(False)
        image_file = QFile(ad_params["image"])
        image_file.open(QFile.ReadOnly)
        file_dict = {
            "image": image_file
        }
        if ad_params["filepath"]:
            pdf_file = QFile(ad_params["filepath"])
            pdf_file.open(QFile.ReadOnly)
            file_dict["pdf_file"] = pdf_file
        text_dict = ad_params.copy()
        multipart_data = generate_multipart_data(text_dict, file_dict)
        # close后便无法生成multipartData
        # image_file.close()
        # if pdf_file:
        #     pdf_file.close()
        url = SERVER_API + 'advertisement/'
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, multipart_data)
        reply.finished.connect(self.create_advertisement_reply)
        multipart_data.setParent(reply)

    def create_advertisement_reply(self):
        """ 创建广告返回 """
        reply = self.sender()
        reply.deleteLater()
        if reply.error():
            print(reply.readAll().data())
            message = "创建新广告失败!"
        else:
            message = "创建新广告成功!"
        p = InformationPopup(message, self)
        p.exec_()
        self.create_button.setEnabled(True)
