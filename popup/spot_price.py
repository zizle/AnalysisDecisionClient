# _*_ coding:utf-8 _*_
# @File  : spot_price.py
# @Time  : 2020-10-14 15:30
# @Author: zizle

""" 首页更多的现货报价弹窗 """
import json
from datetime import datetime
from PyQt5.QtWidgets import (qApp, QDialog, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QTableWidget, QHeaderView,
                             QTableWidgetItem, QFrame)
from PyQt5.QtCore import QDate, Qt, QUrl
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtNetwork import QNetworkRequest
from settings import SERVER_API


class SpotPricePopup(QDialog):
    def __init__(self, *args):
        super(SpotPricePopup, self).__init__(*args)
        self.setFixedSize(800, 500)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("现货报价")
        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        opt_layout.addWidget(self.date_edit)

        self.query_button = QPushButton("查询", self)
        self.query_button.clicked.connect(self.get_sport_prices)
        opt_layout.addWidget(self.query_button)
        opt_layout.addStretch()

        main_layout.addLayout(opt_layout)

        self.spot_price_table = QTableWidget(self)
        self.spot_price_table.setFrameShape(QFrame.NoFrame)
        self.spot_price_table.verticalHeader().hide()
        self.spot_price_table.setColumnCount(5)
        self.spot_price_table.setHorizontalHeaderLabels(["序号", "品种", "日期", "报价", "增减"])
        self.spot_price_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.spot_price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.spot_price_table)
        self.setLayout(main_layout)
        self.spot_price_table.horizontalScrollBar().setStyleSheet(
            "QScrollBar:horizontal{background:transparent;height:10px;margin:0px;}"
            "QScrollBar:horizontal:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:horizontal{background:rgba(0,0,0,50);height:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:horizontal:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-line:horizontal{width:0px}"
            "QScrollBar::add-line:horizontal{width:0px}"
        )
        self.spot_price_table.verticalScrollBar().setStyleSheet(
            "QScrollBar:vertical{background: transparent; width:10px;margin: 0px;}"
            "QScrollBar:vertical:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:vertical{background: rgba(0,0,0,50);width:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:vertical:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-line:vertical{height:0px}"
            "QScrollBar::add-line:vertical{height:0px}"
        )
        self.spot_price_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 #49aa54, stop: 0.48 #49cc54,stop: 0.52 #49cc54, stop:1 #49aa54);"
            "border:1px solid rgb(201,202,202);border-left:none;"
            "min-height:25px;min-width:40px;font-weight:bold;font-size:13px};"
        )

        self.get_sport_prices()

    def get_sport_prices(self):
        """ 请求当前时间的现货报价 """
        current_date = self.date_edit.text()
        current_date = datetime.strptime(current_date, "%Y-%m-%d").strftime("%Y%m%d")
        url = SERVER_API + "spot-price/?date={}".format(current_date)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.spot_price_reply)

    def spot_price_reply(self):
        """ 指定日期现货报价数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_current_sport_prices(data["data"], value_keys=["id", "variety_zh", "date", "spot_price", "price_increase"])
        reply.deleteLater()

    def show_current_sport_prices(self, content_values, value_keys):
        """ 显示数据 """
        self.spot_price_table.clearContents()
        self.spot_price_table.setRowCount(len(content_values))
        for row, row_item in enumerate(content_values):
            for col, key in enumerate(value_keys):
                if col == 0:
                    item = QTableWidgetItem(str(row + 1))
                else:
                    item = QTableWidgetItem(str(row_item[key]))
                if col == 4:  # 设置颜色
                    if int(row_item[key]) > 0:
                        color = QColor(203, 0, 0)
                    elif int(row_item[key]) < 0:
                        color = QColor(0, 124, 0)
                    else:
                        color = QColor(0, 0, 0)
                    item.setForeground(QBrush(color))
                item.setTextAlignment(Qt.AlignCenter)
                self.spot_price_table.setItem(row, col, item)

