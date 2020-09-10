# _*_ coding:utf-8 _*_
# @File  : exchange_spider.py
# @Time  : 2020-07-22 21:00
# @Author: zizle
from PyQt5.QtGui import QIcon
from .exchange_spider_ui import ExchangeSpiderUI
from spiders.czce import CZCESpider, CZCEParser
from spiders.shfe import SHFESpider, SHFEParser
from spiders.cffex import CFFEXSpider, CFFEXParser
from spiders.dce import DCESpider, DCEParser


class ExchangeSpider(ExchangeSpiderUI):
    """ 数据抓取业务 """
    _exchange_lib = {
        "cffex": "中国金融期货交易所",
        "shfe": "上海期货交易所",
        "czce": "郑州商品交易所",
        "dce": "大连商品交易所"
    }
    _actions = {
        "daily": "日交易数据",
        "rank": "日交易排名",
        "receipt": "每日仓单"
    }

    def __init__(self, *args, **kwargs):
        super(ExchangeSpider, self).__init__(*args, **kwargs)

        self.current_exchange = None
        self.current_action = None

        self.spider = None
        self.parser = None

        self.tree_widget.selected_signal.connect(self.selected_action)  # 树控件点击事件
        self.spider_start_button.clicked.connect(self.starting_spider_data)  # 开始抓取
        self.parser_start_button.clicked.connect(self.starting_parser_data)  # 开始解析

    def selected_action(self, exchange, action):
        """ 树控件菜单点击传出信号 """
        self.current_exchange = exchange
        self.current_action = action

        self.spider_exchange_button.setText(self._exchange_lib[exchange])
        self.spider_exchange_button.setIcon(QIcon("icons/" + exchange + "_logo.png"))

        self.parser_exchange_button.setText(self._exchange_lib[exchange])
        self.parser_exchange_button.setIcon(QIcon("icons/" + exchange + "_logo.png"))

        self.spider_action_button.setText(self._actions[action])
        self.spider_action_button.setIcon(QIcon("icons/" + action + ".png"))

        self.parser_action_button.setText(self._actions[action])
        self.parser_action_button.setIcon(QIcon("icons/" + action + ".png"))

        if self.spider is not None:
            self.spider.deleteLater()
            self.spider = None
        if self.parser is not None:
            self.parser.deleteLater()
            self.parser = None

        if self.current_exchange == "czce":
            self.spider = CZCESpider()
            self.parser = CZCEParser()
        elif self.current_exchange == "shfe":
            self.spider = SHFESpider()
            self.parser = SHFEParser()
        elif self.current_exchange == "cffex":
            self.spider = CFFEXSpider()
            self.parser = CFFEXParser()
        elif self.current_exchange == "dce":
            self.spider = DCESpider()
            self.parser = DCEParser()
        else:
            return
        self.spider.spider_finished.connect(self.spider_source_finished)
        self.parser.parser_finished.connect(self.parser_source_finished)

    def spider_source_finished(self, message, can_reconnect):
        """ 当获取源文件爬虫结束返回的信号 """
        self.spider_status.setText(message)
        if can_reconnect:
            self.spider_start_button.clicked.connect(self.starting_spider_data)  # 信号恢复

    def parser_source_finished(self, message, can_reconnect):
        """ 解析数据返回的信号 """
        self.parser_status.setText(message)
        if can_reconnect:
            self.parser_start_button.clicked.connect(self.starting_parser_data)  # 信号恢复

    def starting_spider_data(self):
        """ 点击开始抓取按钮 """
        if self.spider is None:
            self.spider_status.setText("爬取源数据时,软件内部发生了一个错误!")
            return
        self.spider_status.setText("开始获取【" + self._exchange_lib[self.current_exchange] + "】的【" + self._actions[self.current_action] + "】源数据.")
        self.spider_start_button.clicked.disconnect()
        current_date = self.spider_date_edit.text()
        self.spider.set_date(current_date)  # 设置日期
        if self.current_action == "daily":
            self.spider.get_daily_source_file()
        elif self.current_action == "rank":
            self.spider.get_rank_source_file()
        elif self.current_action == "receipt":
            self.spider.get_receipt_source_file()
        else:
            pass

    def starting_parser_data(self):
        if self.parser is None:
            self.parser_status.setText("解析源数据文件时,软件内部发生了一个错误!")
            return
        self.parser_status.setText("开始解析【" + self._exchange_lib[self.current_exchange] + "】的【" + self._actions[self.current_action] + "】源数据.")
        self.parser_start_button.clicked.disconnect()
        current_date = self.parser_date_edit.text()
        self.parser.set_date(current_date)
        if self.current_action == "daily":
            source_data_frame = self.parser.parser_daily_source_file()
            if source_data_frame.empty:
                self.parser_status.setText("结果【" + self._exchange_lib[self.current_exchange] + "】的【日交易行情】数据为空.")
                return
            # 保存数据到服务器数据库
            self.parser.save_daily_server(source_df=source_data_frame)
        elif self.current_action == "rank":
            source_data_frame = self.parser.parser_rank_source_file()
            if source_data_frame.empty:
                self.parser_status.setText("结果【" + self._exchange_lib[self.current_exchange] + "】的【日持仓排名】数据为空.")
                return
            # 保存数据到服务器数据库
            self.parser.save_rank_server(source_df=source_data_frame)
        elif self.current_action == "receipt":
            source_data_frame = self.parser.parser_receipt_source_file()
            if source_data_frame.empty:
                self.parser_status.setText("结果【" + self._exchange_lib[self.current_exchange] + "】的【仓单日报】数据为空.")
                return
            # 保存数据到服务器数据库
            self.parser.save_receipt_server(source_df=source_data_frame)
        else:
            pass
