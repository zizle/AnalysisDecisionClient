# _*_ coding:utf-8 _*_
# @File  : abstract_report.py
# @Time  : 2020-10-15 11:28
# @Author: zizle

""" 各种报告的UI """
import json
from PyQt5.QtWidgets import (qApp, QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QTableWidget, QLabel, QComboBox,
                             QHeaderView, QFrame, QAbstractItemView, QTableWidgetItem)
from PyQt5.QtCore import QDate, Qt, QTime, QRect, QUrl
from PyQt5.QtGui import QPixmap, QPainter, QPalette, QBrush, QColor
from PyQt5.QtNetwork import QNetworkRequest
from utils.constant import VERTICAL_SCROLL_STYLE
from widgets.paginator import Paginator
from widgets.pdf_shower import PDFContentPopup
from settings import STATIC_URL, SERVER_API


class ReportAbstract(QWidget):
    def __init__(self, *args, **kwargs):
        super(ReportAbstract, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        opts_layout = QHBoxLayout()
        self.page_name = QLabel(self)
        main_layout.addWidget(self.page_name, alignment=Qt.AlignTop | Qt.AlignLeft)
        self.date_edit = QDateEdit(self)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        current_hour = QTime.currentTime().hour()
        current_date = QDate.currentDate() if current_hour >= 16 else QDate.currentDate().addDays(-1)
        self.date_edit.setDate(current_date)
        opts_layout.addWidget(self.date_edit)
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.addItem("全部", "0")
        self.variety_combobox.setFixedWidth(100)
        opts_layout.addWidget(self.variety_combobox)
        self.query_button = QPushButton("查询", self)
        opts_layout.addWidget(self.query_button)
        # 分页器
        self.paginator = Paginator(parent=self)
        opts_layout.addWidget(self.paginator)
        opts_layout.addStretch()
        main_layout.addLayout(opts_layout)
        self.report_table = QTableWidget(self)
        self.report_table.verticalHeader().hide()
        self.report_table.horizontalHeader().hide()
        self.report_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.report_table.setFrameShape(QFrame.NoFrame)
        self.report_table.horizontalHeader().setDefaultSectionSize(100)
        self.report_table.setFocusPolicy(Qt.NoFocus)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setShowGrid(False)
        # 选中一行
        # self.report_table.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不能选中
        self.report_table.setSelectionMode(QAbstractItemView.NoSelection)
        # 背景透明
        table_palette = self.report_table.palette()
        table_palette.setBrush(QPalette.Base, QBrush(QColor(255,255,255,0)))
        self.report_table.setPalette(table_palette)
        self.report_table.setCursor(Qt.PointingHandCursor)
        self.report_table.verticalScrollBar().setStyleSheet(VERTICAL_SCROLL_STYLE)
        main_layout.addWidget(self.report_table)
        self.setLayout(main_layout)
        self.page_name.setObjectName("pageName")
        self.report_table.setObjectName("reportTable")
        self.setStyleSheet(
            "#pageName{color:rgb(233,66,66);font-style:italic;font-size:15px}"
            "#reportTable::item:hover{color:rgb(248,121,27)}"
        )
        self.get_all_variety()  # 获取所有品种
        # 点击事件
        self.report_table.cellClicked.connect(self.view_detail_report)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("media/beijing.jpg"), QRect())

    def get_all_variety(self):
        """ 获取系统中所有的品种 """
        url = SERVER_API + "variety/all/"
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.all_variety_reply)

    def all_variety_reply(self):
        """ 获取所有品种返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            for group_name, group_varieties in data["varieties"].items():
                for variety_item in group_varieties:
                    self.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
        reply.deleteLater()

    def set_page_name(self, name: str):
        self.page_name.setText(name)

    def show_report_content(self, reports):
        """ 显示报告 """
        header_keys = ["title", "date"]
        self.report_table.setColumnCount(len(header_keys))
        self.report_table.setRowCount(len(reports))
        # QHeaderView
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(reports):
            for col, col_key in enumerate(header_keys):
                item = QTableWidgetItem(str(row_item[col_key]))
                if col == 0:
                    item.setData(Qt.UserRole, row_item["filepath"])
                self.report_table.setItem(row, col, item)

    def view_detail_report(self, row, col):
        """ 查看报告内容 """
        item = self.report_table.item(row, 0)
        file_url = STATIC_URL + item.data(Qt.UserRole)
        p = PDFContentPopup(file=file_url, title=item.text(), parent=self)
        p.exec_()
