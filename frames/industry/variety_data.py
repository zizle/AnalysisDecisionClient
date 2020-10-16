# _*_ coding:utf-8 _*_
# @File  : variety_data.py
# @Time  : 2020-09-03 8:29
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl
from settings import SERVER_API, logger
from utils.client import get_user_token
from popup.sheet_charts import SheetChartsPopup
from .variety_data_ui import VarietyDataUI, OperateButton


class VarietyData(VarietyDataUI):
    def __init__(self, *args, **kwargs):
        super(VarietyData, self).__init__(*args, **kwargs)
        self.variety_tree.left_mouse_clicked.connect(self.selected_variety_event)
        # 默认显示股指的数据
        self._get_variety_sheets("GP")
        # 默认加载主页显示的图形
        self._load_default_page()
        # 双击数据库下的条目
        self.sheet_table.doubleClicked.connect(self.popup_show_chart_sheet)

    def _load_default_page(self):
        """ 加载主页默认页面 """
        url = SERVER_API + "industry/chart/"
        self.chart_container.load(QUrl(url))

    def selected_variety_event(self, variety_id, group_text, variety_en):
        """ 选择了某个品种事件 """
        self._get_variety_sheets(variety_en)
        self._load_variety_charts(variety_en)

    def _load_variety_charts(self, variety_en):
        """ 加载品种下的所有数据图 """
        uset_token = get_user_token().split(' ')[1]
        url = SERVER_API + "variety/{}/chart/?render=1&is_petit=1&token={}".format(variety_en, uset_token)
        self.chart_container.load(QUrl(url))

    def _get_variety_sheets(self, variety_en):
        """ 获取当前品种下的数据表 """
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "variety/{}/sheet/".format(variety_en)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.variety_sheets_reply)

    def variety_sheets_reply(self):
        """ 请求到品种数据表 """
        reply = self.sender()
        if reply.error():
            logger.error("产业数据库主页获取数据表失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            self.sheet_table_show_contents(data["sheets"])

    def sheet_table_show_contents(self, sheets):
        """ 数据列表显示 """
        self.sheet_table.clearContents()
        self.sheet_table.setRowCount(len(sheets))
        for row, row_item in enumerate(sheets):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setData(Qt.UserRole, row_item["id"])
            item0.setTextAlignment(Qt.AlignCenter)
            self.sheet_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["sheet_name"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.sheet_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["min_date"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.sheet_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["max_date"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.sheet_table.setItem(row, 3, item3)

            item4_button = OperateButton("media/icons/chart.png", "media/icons/chart_hover.png", self)
            setattr(item4_button, "row_index", row)
            item4_button.clicked.connect(self.show_sheet_charts)
            self.sheet_table.setCellWidget(row, 4, item4_button)

    def popup_show_chart_sheet(self):
        """ 弹窗显示某个表下的所有图形和表数据"""
        self.show_sheet_charts(self.sheet_table.currentRow())

    def show_sheet_charts(self, current_row=False):
        """ 弹窗显示某个表下的所有图形和表数据 """
        if current_row is False:
            current_row = getattr(self.sender(), "row_index")
        sheet_id = self.sheet_table.item(current_row, 0).data(Qt.UserRole)
        sheet_name = self.sheet_table.item(current_row, 1).text()
        popup = SheetChartsPopup(sheet_id, 0, self)
        popup.setWindowTitle(sheet_name)
        popup.exec_()
