# _*_ coding:utf-8 _*_
# @File  : monthly_report.py
# @Time  : 2020-10-15 14:38
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QUrl
from .abstract_report import ReportAbstract
from settings import SERVER_API


class AnnualReport(ReportAbstract):
    def __init__(self, *args, **kwargs):
        super(AnnualReport, self).__init__(*args, **kwargs)
        self.set_page_name("年度报告")
        self.date_edit.hide()  # 隐藏日期
        # 获取报告
        self.get_annual_reports()
        # 点击查询
        self.query_button.clicked.connect(self.get_annual_reports)
        # 点击页码的事件
        self.paginator.clicked.connect(self.get_annual_reports)

    def get_annual_reports(self):
        """ 分页查询月报数据 """
        current_page = self.paginator.get_current_page()
        current_variety = self.variety_combobox.currentData()
        url = SERVER_API + "report-file/paginator/?report_type=annual&variety_en={}&page={}&page_size=50".format(current_variety, current_page)
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