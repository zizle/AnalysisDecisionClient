# _*_ coding:utf-8 _*_
# @File  : cffex.py
# @Time  : 2020-07-31 9:37
# @Author: zizle
import os
import json
import time
import random
from datetime import datetime
from pandas import DataFrame, read_csv, concat, read_excel
from PyQt5.QtWidgets import qApp
from PyQt5.QtCore import QObject, pyqtSignal, QFile, QEventLoop, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from utils.characters import split_number_en
from configs import USER_AGENTS, LOCAL_SPIDER_SRC, SERVER
from settings import logger

VARIETY_LIST = ["IF", "IC", "IH", "TS", "TF", "T"]


class DateValueError(Exception):
    """ 日期错误 """


class CFFEXSpider(QObject):
    spider_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(CFFEXSpider, self).__init__(*args, **kwargs)
        self.date = None
        self.event_loop = QEventLoop(self)  # 用于网络请求同步事件阻塞

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def get_daily_source_file(self):
        """ 获取每日行情数据源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCESpider`日期.")
        url = "http://www.cffex.com.cn/sj/hqsj/rtj/{}/{}/{}_1.csv".format(self.date.strftime('%Y%m'), self.date.strftime('%d'), self.date.strftime('%Y%m%d'))

        network_manager = getattr(qApp, "_network")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.daily_source_file_reply)

    def daily_source_file_reply(self):
        """ 获取日统计数据请求返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'cffex/daily/{}.csv'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取中金所{}日交易数据源文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_rank_source_file(self):
        """ 获取日排名数据源文件 """
        base_url = "http://www.cffex.com.cn/sj/ccpm/{}/{}/{}_1.csv"
        network_manager = getattr(qApp, "_network")

        for variety in VARIETY_LIST:
            url = base_url.format(self.date.strftime("%Y%m"), self.date.strftime("%d"), variety)
            self.spider_finished.emit("准备获取{}的日排名数据文件...".format(variety), False)
            request = QNetworkRequest(QUrl(url))
            request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
            reply = network_manager.get(request)
            reply.finished.connect(self.rank_source_file_reply)
            time.sleep(1)
            self.event_loop.exec_()

    def rank_source_file_reply(self):
        """ 获取日排名请求返回 """
        reply = self.sender()
        request_url = reply.request().url().url()
        # 解析出请求的品种
        request_filename = request_url.rsplit("/", 1)[1]
        request_variety = request_filename.split("_")[0]
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("获取{}排名数据文件。\n失败:{}".format(request_variety[:2], str(reply.error())), True)
            logger.error("获取{}排名数据文件失败了!".format(request_url[:2]))
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'cffex/rank/{}_{}.csv'.format(request_variety, self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        tip = "获取中金所{}_{}日持仓排名数据保存到文件成功!".format(request_variety, self.date.strftime("%Y-%m-%d"))
        if request_variety == "T":
            tip = "获取中金所{}日所有品种持仓排名数据保存到文件成功!".format(self.date.strftime("%Y-%m-%d"))
        self.spider_finished.emit(tip, True)
        self.event_loop.quit()


class CFFEXParser(QObject):
    parser_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(CFFEXParser, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def parser_daily_source_file(self):
        """ 解析日统计源文件数据到DataFrame """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'cffex/daily/{}.csv'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现中金所{}的日交易统计文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        csv_df = read_csv(file_path, encoding='gbk', error_bad_lines=False)
        # print(csv_df.columns.values.tolist())
        # if csv_df.columns.values.tolist() != ['合约代码', '今开盘', '最高价', '最低价', '成交量',
        # '成交金额', '持仓量', '今收盘', '今结算', '涨跌1', '涨跌2', 'Delta']:
        #     self.parser_finished.emit("中金所{}的日交易统计文件数据格式有误".format(self.date.strftime("%Y-%m-%d")), True)
        #     return DataFrame()
        csv_df = csv_df[~csv_df['合约代码'].str.contains('-C-|-P-|小计|合计')]  # 去除合约代码-C- -P-的期权数据 小计 合计总计数据
        csv_df["合约代码"] = csv_df["合约代码"].str.strip()  # 去除前后空格
        csv_df["成交金额"] = csv_df["成交金额"].round(decimals=6)  # 成交金额保留6位小数
        csv_df["品种"] = csv_df["合约代码"].apply(split_number_en).apply(lambda x: x[0].upper())  # 使用合约代码列添加品种列
        str_date = self.date.strftime("%Y%m%d")
        csv_df["日期"] = [str_date for _ in range(csv_df.shape[0])]  # 增加日期列
        # 重置索引
        csv_df = csv_df.reindex(columns=["日期", "品种", "合约代码", "今开盘", "最高价", "最低价", "今收盘",
                                "今结算", "涨跌1", "涨跌2", "成交量", "成交金额", "持仓量"])
        csv_df.columns = ["date", "variety_en", "contract", "open_price", "highest", "lowest", "close_price",
                          "settlement", "zd_1", "zd_2", "trade_volume", "trade_price", "empty_volume"]
        # 填充空值
        csv_df[
            ["open_price", "highest", "lowest", "close_price", "settlement", "zd_1", "zd_2", "trade_volume", "trade_price", "empty_volume"]
        ] = csv_df[
            ["open_price", "highest", "lowest", "close_price", "settlement", "zd_1", "zd_2", "trade_volume", "trade_price", "empty_volume"]
        ].fillna(0)
        return csv_df

    def save_daily_server(self, source_df):
        """ 保存日行情数据到服务器 """
        self.parser_finished.emit("开始保存中金所{}日交易数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER + "exchange/cffex/daily/?date=" + self.date.strftime("%Y-%m-%d")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")

        reply = network_manager.post(request, json.dumps(data_body).encode("utf-8"))
        reply.finished.connect(self.save_daily_server_reply)

    def save_daily_server_reply(self):
        """ 保存数据到交易所返回响应 """
        reply = self.sender()
        data = reply.readAll().data()
        reply.deleteLater()
        if reply.error():
            self.parser_finished.emit("保存中金所{}日交易数据到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode('utf-8'))
            self.parser_finished.emit(data["message"], True)

    def parser_rank_source_file(self):
        """ 解析源文件数据为pandas的DataFrame """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")

        result_df = DataFrame(columns=[])
        for variety in VARIETY_LIST:
            file_path = os.path.join(LOCAL_SPIDER_SRC, 'cffex/rank/{}_{}.csv'.format(variety, self.date.strftime("%Y-%m-%d")))
            if not os.path.exists(file_path):
                self.parser_finished.emit("没有发现中金所{}_{}的日排名文件,请先抓取数据!".format(variety, self.date.strftime("%Y-%m-%d")), True)
                logger.error("没有发现中金所{}_{}的日排名源文件".format(variety, self.date.strftime("%Y-%m-%d")))
                return DataFrame()
            variety_df = self.parser_variety_rank_file(file_path, variety)
            result_df = concat([result_df, variety_df])
        return result_df

    def parser_variety_rank_file(self, file_path, variety_name):
        """ 使用pandas解析中金所品种的日排名数据 """
        if variety_name in ["TF", "T"]:  # 5年期和10年期国债从2020-09-14日起多公布了非期货公司的量,占用第1,2行
            variety_df = read_csv(file_path, encoding="gbk", skiprows=[0, 1, 3])
        else:
            variety_df = read_csv(file_path, encoding="gbk", skiprows=[1])

        if variety_df.columns.values.tolist() != ['交易日', '合约', '排名', '成交量排名', 'Unnamed: 4', 'Unnamed: 5', '持买单量排名',
                                                  'Unnamed: 7', 'Unnamed: 8', '持卖单量排名', 'Unnamed: 10', 'Unnamed: 11']:
            logger.error("中金所{}_{}的日排名源文件格式有误".format(variety_name, self.date.strftime("%Y-%m-%d")))
            return DataFrame()
        # 重置头名
        variety_df.columns = ["date", "contract", "rank", "trade_company", "trade", "trade_increase",
                              "long_position_company", "long_position", "long_position_increase",
                              "short_position_company", "short_position", "short_position_increase"]
        # 处理字符串前后空格
        variety_df["contract"] = variety_df["contract"].str.strip()
        variety_df["trade_company"] = variety_df["trade_company"].str.strip()
        variety_df["long_position_company"] = variety_df["long_position_company"].str.strip()
        variety_df["short_position_company"] = variety_df["short_position_company"].str.strip()
        # 插入品种列
        variety_df["variety_en"] = [variety_name for _ in range(variety_df.shape[0])]
        # 重置列索引
        variety_df = variety_df.reindex(columns=["date", "variety_en", "contract", "rank",
                                                 "trade_company", "trade", "trade_increase",
                                                 "long_position_company", "long_position", "long_position_increase",
                                                 "short_position_company", "short_position", "short_position_increase"])
        return variety_df

    def save_rank_server(self, source_df):
        """ 保存日持仓排名到服务器 """
        self.parser_finished.emit("开始保存中金所{}日持仓排名数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER + "exchange/cffex/rank/?date=" + self.date.strftime("%Y-%m-%d")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")

        reply = network_manager.post(request, json.dumps(data_body).encode("utf-8"))
        reply.finished.connect(self.save_rank_server_reply)

    def save_rank_server_reply(self):
        """ 保存日持仓排名到数据库返回 """
        reply = self.sender()
        data = reply.readAll().data()
        reply.deleteLater()
        if reply.error():
            self.parser_finished.emit("保存中金所{}日持仓排名到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)
