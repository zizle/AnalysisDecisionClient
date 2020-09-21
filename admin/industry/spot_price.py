# _*_ coding:utf-8 _*_
# @File  : basis_price.py
# @Time  : 2020-08-25 15:01
# @Author: zizle
import re
import json
from datetime import datetime
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QPushButton, QAbstractItemView
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtNetwork import QNetworkRequest
from .spot_price_ui import SpotPriceAdminUI
from utils.constant import VARIETY_EN
from settings import SERVER_API


class SpotPriceAdmin(SpotPriceAdminUI):
    def __init__(self, *args, **kwargs):
        super(SpotPriceAdmin, self).__init__(*args, **kwargs)
        self.final_data = list()   # 最终现货数据
        self.today_str = ""
        self.analysis_button.clicked.connect(self.extract_spot_source_price)  # 提取数据
        self.commit_button.clicked.connect(self.commit_spot_data)             # 上传提交数据

        self.modify_query_button.clicked.connect(self.query_spot_data)        # 查询现货报价数据

    def extract_spot_source_price(self):
        """ 提取现货数据 """
        self.final_data.clear()
        current_date = self.current_date.text()
        self.today_str = datetime.strptime(current_date, "%Y-%m-%d").strftime("%Y%m%d")
        source_str = self.source_edit.text().strip()
        if not source_str:
            self.tip_label.setText("请输入源数据再进行提取! ")
            return
        self.tip_label.setText("正在提取数据... ")
        variety_item_list = re.split(r'[;；。]+', source_str)  # 根据分号切割
        self.preview_table.clearContents()
        self.preview_table.setRowCount(0)
        for row, variety_item in enumerate(variety_item_list):
            print(variety_item)
            data_list = re.split(r'[:,：，]+', variety_item)
            variety_dict = {
                "date": self.today_str,
                "variety_en": VARIETY_EN.get(data_list[0].strip(), "未知"),
                "spot_price": float(data_list[1]),
                "price_increase": float(data_list[2])
            }

            self.preview_table.insertRow(row)
            item0 = QTableWidgetItem(variety_dict["date"])
            self.preview_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(data_list[0].strip())
            self.preview_table.setItem(row, 1, item1)
            item2 = QTableWidgetItem(variety_dict["variety_en"])
            self.preview_table.setItem(row, 2, item2)
            item3 = QTableWidgetItem(str(variety_dict["spot_price"]))
            self.preview_table.setItem(row, 3, item3)
            item4 = QTableWidgetItem(str(variety_dict["price_increase"]))
            self.preview_table.setItem(row, 4, item4)
            if variety_dict["variety_en"] == "未知":
                item0.setForeground(QBrush(QColor(250, 100, 100)))
                item1.setForeground(QBrush(QColor(250, 100, 100)))
                item2.setForeground(QBrush(QColor(250, 100, 100)))
                item3.setForeground(QBrush(QColor(250, 100, 100)))
                item4.setForeground(QBrush(QColor(250, 100, 100)))

            self.final_data.append(variety_dict)
        self.tip_label.setText("数据提取完成! ")

    def commit_spot_data(self):
        """ 提交数据 """
        self.tip_label.setText("正在上传数据到服务器...")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "spot-price/?date=" + self.today_str
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")

        reply = network_manager.post(request, json.dumps(self.final_data).encode("utf-8"))
        reply.finished.connect(self.save_spot_price_reply)

    def save_spot_price_reply(self):
        """ 保存数据返回 """
        reply = self.sender()
        data = reply.readAll().data()
        reply.deleteLater()
        if reply.error():
            self.tip_label.setText("保存{}现货动态数据数据库失败:{}".format(self.today_str, reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.tip_label.setText(data["message"])
        self.preview_table.clearContents()
        self.preview_table.setRowCount(0)
        self.source_edit.clear()

    def query_spot_data(self):
        """ 查询指定日期现货数据用于修改 """
        query_date = self.modify_date_edit.text()
        query_date_str = datetime.strptime(query_date, "%Y-%m-%d").strftime("%Y%m%d")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "spot-price/?date=" + query_date_str

        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.query_spot_price_reply)

    def query_spot_price_reply(self):
        """ 获取指定日期现货数据返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            self.modify_tip_label.setText("获取{}现货动态数据失败:\n{}".format(self.modify_date_edit.text(), reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.modify_tip_label.setText(data["message"])
        reply.deleteLater()
        self.modify_table.clearContents()
        self.modify_table.setRowCount(0)
        for row, row_item in enumerate(data["data"]):
            self.modify_table.insertRow(row)
            item0 = QTableWidgetItem(str(row_item["id"]))
            item1 = QTableWidgetItem(row_item["date"])
            item2 = QTableWidgetItem(row_item["variety_en"])
            item3 = QTableWidgetItem(str(row_item["spot_price"]))
            item4 = QTableWidgetItem(str(row_item["price_increase"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item1.setTextAlignment(Qt.AlignCenter)
            item2.setTextAlignment(Qt.AlignCenter)
            item3.setTextAlignment(Qt.AlignCenter)
            item4.setTextAlignment(Qt.AlignCenter)
            # ID 日期 品种不支持修改
            item0.setFlags(Qt.ItemIsEditable)
            item0.setForeground(QBrush(QColor(50, 50, 50)))
            item1.setFlags(Qt.ItemIsEditable)
            item1.setForeground(QBrush(QColor(50, 50, 50)))
            item2.setFlags(Qt.ItemIsEditable)
            item2.setForeground(QBrush(QColor(50, 50, 50)))
            self.modify_table.setItem(row, 0, item0)
            self.modify_table.setItem(row, 1, item1)
            self.modify_table.setItem(row, 2, item2)
            self.modify_table.setItem(row, 3, item3)
            self.modify_table.setItem(row, 4, item4)
            m_button = QPushButton("确定", self)
            m_button.setObjectName("modifyButton")
            m_button.setCursor(Qt.PointingHandCursor)
            setattr(m_button, 'row_index', row)
            m_button.clicked.connect(self.modify_row_data)
            self.modify_table.setCellWidget(row, 5, m_button)

    def modify_row_data(self):
        """ 修改数据表的单元格点击 """
        btn = self.sender()
        row = getattr(btn, 'row_index')
        # 获取组织数据
        item = {
            "id": int(self.modify_table.item(row, 0).text()),
            "date": self.modify_table.item(row, 1).text(),
            "variety_en": self.modify_table.item(row, 2).text(),
            "spot_price": float(self.modify_table.item(row, 3).text()),
            "price_increase": float(self.modify_table.item(row, 4).text())
        }
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "spot-price/{}/".format(item["id"])

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")

        reply = network_manager.put(request, json.dumps(item).encode("utf-8"))
        reply.finished.connect(self.modify_spot_price_reply)

    def modify_spot_price_reply(self):
        """ 修改数据返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            self.modify_tip_label.setText("修改数据失败:\n{}".format(self.modify_date_edit.text(), reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.modify_tip_label.setText(data["message"])
        reply.deleteLater()
