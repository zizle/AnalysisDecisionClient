# _*_ coding:utf-8 _*_
# @File  : sheet_charts.py
# @Time  : 2020-09-08 10:19
# @Author: zizle

""" 表的图形弹窗 """
import json
import pandas as pd
from PyQt5.QtWidgets import (qApp, QWidget,QTableWidget, QTableWidgetItem, QSplitter, QDialog, QVBoxLayout, QDesktopWidget, QAbstractItemView,
                             QHeaderView, QTextEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebChannel import QWebChannel
from channels.chart import ChartOptionChannel
from utils.client import get_user_token
from settings import SERVER_API, logger


class SheetChartsPopup(QDialog):
    def __init__(self, sheet_id: int, is_own: int, *args, **kwargs):
        super(SheetChartsPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.sheet_id = sheet_id
        print(sheet_id)

        # 初始化大小
        available_size = QDesktopWidget().availableGeometry()  # 用户的桌面信息,来改变自身窗体大小
        available_width, available_height = available_size.width(), available_size.height()
        self.resize(available_width * 0.66, available_height * 0.72)

        main_layout = QVBoxLayout()
        main_splitter = QSplitter(self)
        main_splitter.setOrientation(Qt.Vertical)

        self.chart_container = QWebEngineView(self)
        user_token = get_user_token().split(' ')[1]
        charts_url = SERVER_API + "sheet/{}/chart/?is_own={}&token={}".format(self.sheet_id, is_own, user_token)
        self.chart_container.load(QUrl(charts_url))
        main_splitter.addWidget(self.chart_container)

        self.sheet_table = QTableWidget(self)
        self.sheet_table.verticalHeader().hide()
        self.sheet_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_splitter.addWidget(self.sheet_table)
        main_splitter.setSizes([available_height * 0.43, available_height * 0.3])  # 初始化大小

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        self.sheet_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 #bbbbbb, stop: 0.5 #eeeeee,stop: 0.6 #eeeeee, stop:1 #bbbbbb);"
            "border:1px solid rgb(201,202,202);border-left:none;"
            "min-height:25px;min-width:40px;font-weight:bold;font-size:13px};"
        )

        self._get_sheet_values()

    def _get_sheet_values(self):
        """ 获取表格原始数据 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "sheet/{}/".format(self.sheet_id)
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.sheet_values_reply)

    def sheet_values_reply(self):
        """ 获取到数据表数据 """
        reply = self.sender()
        if reply.error():
            logger.error("用户获取数据表源数据失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            # 使用pandas处理数据到弹窗表格中
            self.handler_sheet_values(data["sheet_values"])

    def handler_sheet_values(self, values):
        """ pandas处理数据到弹窗相应参数中 """
        value_df = pd.DataFrame(values)
        print(value_df)
        sheet_headers = value_df.iloc[:1].to_numpy().tolist()[0]  # 取表头
        sheet_headers.pop(0)  # 删掉id列
        col_index_list = ["id", ]
        for i, header_item in enumerate(sheet_headers):  # 根据表头生成数据选择项
            col_index_list.append("column_{}".format(i))
        sheet_headers.insert(0, "编号")
        self.sheet_table.setColumnCount(len(sheet_headers))
        self.sheet_table.setHorizontalHeaderLabels(sheet_headers)
        self.sheet_table.horizontalHeader().setDefaultSectionSize(150)
        self.sheet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.sheet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        table_show_df = value_df.iloc[1:]
        table_show_df = table_show_df.sort_values(by="column_0")
        table_show_df.reset_index(inplace=True)  # 重置索引,让排序生效(赋予row正确的值)
        self.sheet_table.setRowCount(table_show_df.shape[0])
        for row, row_item in table_show_df.iterrows():  # 遍历数据(填入表格显示)
            for col, col_key in enumerate(col_index_list):
                item = QTableWidgetItem(str(row_item[col_key]))
                item.setTextAlignment(Qt.AlignCenter)
                self.sheet_table.setItem(row, col, item)


class DeciphermentPopup(QWidget):
    """ 编辑解说的弹窗 """
    def __init__(self, chart_id, *args, **kwargs):
        super(DeciphermentPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlag(Qt.Dialog)
        self.setWindowTitle("解读图形")
        self.resize(380, 200)
        self.chart_id = chart_id
        main_layout = QVBoxLayout()
        self.decipherment_edit = QTextEdit(self)
        main_layout.addWidget(self.decipherment_edit)
        commit_button = QPushButton("确定", self)
        commit_button.clicked.connect(self.commit_current_decipherment)
        main_layout.addWidget(commit_button, alignment=Qt.AlignRight)
        self.setLayout(main_layout)

        self._get_chart_base_information()

    def _get_chart_base_information(self):
        """ 获取图形的基本信息 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "chart/{}/".format(self.chart_id)
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.base_information_reply)

    def base_information_reply(self):
        """ 获取基本信息返回 """
        reply = self.sender()
        if reply.error():
            self.decipherment_edit.setPlaceholderText("获取信息失败了......")
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            chart_info = data["data"]
            self.decipherment_edit.setText(chart_info["decipherment"])
        reply.deleteLater()

    def commit_current_decipherment(self):
        """ 上传当前的图形解读 """
        decipherment = self.decipherment_edit.toPlainText()
        body = {
            "decipherment": decipherment
        }

        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "chart-decipherment/{}/".format(self.chart_id)
        reply = network_manager.put(QNetworkRequest(QUrl(url)), json.dumps(body).encode("utf-8"))
        reply.finished.connect(self.commit_decipherment_reply)

    def commit_decipherment_reply(self):
        """ 修改解读返回 """
        reply = self.sender()
        if not reply.error():
            QMessageBox.information(self, "成功", "修改成功!")
        self.close()


class ChartPopup(QWidget):
    """ 显示某个图形 """
    def __init__(self, chart_id, *args, **kwargs):
        super(ChartPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlag(Qt.Dialog)
        self.resize(680, 380)
        self.chart_id = chart_id
        main_layout = QVBoxLayout()
        self.chart_container = QWebEngineView(self)
        self.chart_container.load(QUrl("file:///html/charts/custom_chart.html"))

        # 设置与页面信息交互的通道
        channel_qt_obj = QWebChannel(self.chart_container.page())  # 实例化qt信道对象,必须传入页面参数
        self.contact_channel = ChartOptionChannel()  # 页面信息交互通道
        self.chart_container.page().setWebChannel(channel_qt_obj)
        channel_qt_obj.registerObject("pageContactChannel", self.contact_channel)  # 信道对象注册信道，只能注册一个

        main_layout.addWidget(self.chart_container)
        self.setLayout(main_layout)
        self.chart_container.loadFinished.connect(self._get_chart_option_values)

    def _get_chart_option_values(self):
        """ 获取图形的配置和数据 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "chart-option/{}/".format(self.chart_id)
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.chart_option_values_reply)

    def chart_option_values_reply(self):
        """ 获取图形的配置和数据返回 """
        reply = self.sender()
        if reply.error():
            logger.error("用户获取单个图形配置和数据错误:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            chart_type = data["chart_type"]
            base_option = data["base_option"]
            chart_values = data["chart_values"]
            self.contact_channel.chartSource.emit(chart_type, json.dumps(base_option), json.dumps(chart_values))
        reply.deleteLater()

