# _*_ coding:utf-8 _*_
# @File  : daily_report.py
# @Time  : 2020-10-15 09:37
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QHeaderView
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl
from widgets.pdf_shower import PDFContentPopup
from settings import SERVER_API, STATIC_URL
from .abstract_report import ReportAbstract


class DailyReport(ReportAbstract):
    def __init__(self, *args, **kwargs):
        super(DailyReport, self).__init__(*args, **kwargs)
        self.set_page_name("收盘评论")
        # 隐藏分页器
        self.paginator.hide()
        self.get_current_report()  # 获取当前报告
        # 点击查询
        self.query_button.clicked.connect(self.get_current_report)

    def get_current_report(self):
        """ 获取当前日期的日报告"""
        current_date = self.date_edit.text()
        variety_en = self.variety_combobox.currentData()
        url = SERVER_API + 'report-file/?query_date={}&report_type=daily&variety_en={}'.format(current_date, variety_en)
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.current_report_reply)

    def current_report_reply(self):
        """ 当前报告返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_report_content(data["reports"])
        reply.deleteLater()
