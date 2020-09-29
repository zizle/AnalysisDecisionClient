# _*_ coding:utf-8 _*_
# @File  : shfe.py
# @Time  : 2020-07-28 8:57
# @Author: zizle
import os
import json
import random
import numpy as np
from datetime import datetime
from pandas import DataFrame
from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import qApp
from PyQt5.QtNetwork import QNetworkRequest
from utils.characters import split_number_en, full_width_to_half_width
from utils.constant import VARIETY_EN
from settings import USER_AGENTS, LOCAL_SPIDER_SRC, SERVER_API, logger


class DateValueError(Exception):
    """ 日期错误 """


class SHFESpider(QObject):
    spider_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(SHFESpider, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def get_daily_source_file(self):
        """ 获取日交易源数据保存至json文件 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`SHFESpider`日期.")
        url = "http://www.shfe.com.cn/data/dailydata/kx/kx{}.dat".format(self.date.strftime('%Y%m%d'))

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.daily_source_file_reply)

    def daily_source_file_reply(self):
        """ 获取日交易源数据返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'shfe/daily/{}.json'.format(self.date.strftime("%Y-%m-%d")))
        with open(save_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        reply.deleteLater()
        self.spider_finished.emit("获取上期所{}日交易数据保存到文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_rank_source_file(self):
        """ 获取日排名数据 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`SHFESpider`日期.")
        url = "http://www.shfe.com.cn/data/dailydata/kx/pm{}.dat".format(self.date.strftime('%Y%m%d'))

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.rank_source_file_reply)

    def rank_source_file_reply(self):
        """ 获取日排名请求返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'shfe/rank/{}.json'.format(self.date.strftime("%Y-%m-%d")))
        with open(save_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        reply.deleteLater()
        self.spider_finished.emit("获取上期所{}日持仓排名数据保存到文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_receipt_source_file(self):
        """ 获取仓单日报数据源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`SHFESpider`日期.")
        url = "http://www.shfe.com.cn/data/dailydata/{}dailystock.dat".format(self.date.strftime('%Y%m%d'))
        network_manager = getattr(qApp, "_network")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.receipt_source_file_reply)

    def receipt_source_file_reply(self):
        """ 每日仓单数据返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'shfe/receipt/{}.json'.format(self.date.strftime("%Y-%m-%d")))
        with open(save_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        reply.deleteLater()
        self.spider_finished.emit("获取上期所{}每日仓单数据保存到文件成功!".format(self.date.strftime("%Y-%m-%d")), True)


class SHFEParser(QObject):
    parser_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(SHFEParser, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def parser_daily_source_file(self):
        """ 解析保存的json文件信息 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'shfe/daily/{}.json'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现上期所{}的日交易行情文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        with open(file_path, "r", encoding="utf-8") as reader:
            source_content = json.load(reader)
        # 解析content转为DataFrame
        json_df = DataFrame(source_content['o_curinstrument'])

        # 选取PRODUCTID非总计、DELIVERYMONTH非小计的行
        json_df = json_df[~json_df['PRODUCTID'].str.contains('总计|小计|合计')]  # 选取品种不含有小计和总计合计的行
        json_df = json_df[~json_df['DELIVERYMONTH'].str.contains('总计|小计|合计')]  # 选取合约不含有小计和总计合计的行
        # 处理空格
        json_df["PRODUCTID"] = json_df["PRODUCTID"].apply(lambda x: x.split("_")[0].upper())
        # json_df["PRODUCTGROUPID"] = json_df["PRODUCTGROUPID"].str.strip().str.upper()
        json_df["PRODUCTNAME"] = json_df["PRODUCTNAME"].str.strip()
        json_df["DELIVERYMONTH"] = json_df["DELIVERYMONTH"].str.strip()
        # 提取有用的列
        # json_df = json_df[["PRODUCTGROUPID", "DELIVERYMONTH", "PRESETTLEMENTPRICE", "OPENPRICE", "HIGHESTPRICE", "LOWESTPRICE", "CLOSEPRICE",
        #                    "SETTLEMENTPRICE", "ZD1_CHG", "ZD2_CHG", "VOLUME", "OPENINTEREST", "OPENINTERESTCHG"]]

        json_df = json_df.reindex(columns=["DATE", "PRODUCTID", "DELIVERYMONTH", "PRESETTLEMENTPRICE", "OPENPRICE", "HIGHESTPRICE", "LOWESTPRICE", "CLOSEPRICE",
                                           "SETTLEMENTPRICE", "ZD1_CHG", "ZD2_CHG", "VOLUME", "OPENINTEREST", "OPENINTERESTCHG"])
        str_date = self.date.strftime("%Y%m%d")
        json_df["DATE"] = [str_date for _ in range(json_df.shape[0])]
        # 修改列头，返回
        json_df.columns = ["date", "variety_en", "contract", "pre_settlement", "open_price", "highest", "lowest", "close_price",
                           "settlement", "zd_1", "zd_2", "trade_volume", "empty_volume", "increase_volume"]
        # 合约等于品种+合约
        json_df["contract"] = json_df["variety_en"] + json_df["contract"]
        # 处理没有数据或空值=补0
        json_df.replace(to_replace="^\s*$", value=np.nan, regex=True, inplace=True)
        json_df = json_df.fillna(0)
        return json_df

    def save_daily_server(self, source_df):
        """ 将数据保存到服务器数据库 """
        self.parser_finished.emit("开始保存上期所{}日交易数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/shfe/daily/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存上期所{}日交易数据到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode('utf-8'))
            self.parser_finished.emit(data["message"], True)

    def parser_rank_source_file(self):
        """ 解析日持仓排名json文件 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'shfe/rank/{}.json'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现上期所所{}的日持仓排名文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        with open(file_path, "r", encoding="utf-8") as reader:
            source_content = json.load(reader)
        json_df = DataFrame(source_content["o_cursor"])
        # 取排名在(-1,0,1~20的数据[-1:期货公司总计,0:非期货公司总计,999品种合约总计]
        json_df = json_df[json_df['RANK'] <= 20]
        # 去除字符串空格
        json_df["INSTRUMENTID"] = json_df["INSTRUMENTID"].str.strip().str.upper().str.replace("ALL", '')
        json_df["PARTICIPANTABBR1"] = json_df["PARTICIPANTABBR1"].str.strip()
        json_df["PARTICIPANTABBR2"] = json_df["PARTICIPANTABBR2"].str.strip()
        json_df["PARTICIPANTABBR3"] = json_df["PARTICIPANTABBR3"].str.strip()
        # 空值处理补0
        json_df.replace(to_replace="^\s*$", value=np.nan, regex=True, inplace=True)
        json_df = json_df.fillna(0)
        # 新增品种代码列和DATE列
        json_df["VARIETYEN"] = json_df["INSTRUMENTID"].apply(split_number_en).apply(lambda x: x[0].upper())
        str_date = self.date.strftime("%Y%m%d")
        json_df["DATE"] = [str_date for _ in range(json_df.shape[0])]
        # 重新设置索引
        json_df = json_df.reindex(columns=["DATE", "VARIETYEN", "INSTRUMENTID", "RANK", "PARTICIPANTABBR1", "CJ1", "CJ1_CHG", "PARTICIPANTABBR2", "CJ2", "CJ2_CHG","PARTICIPANTABBR3", "CJ3", "CJ3_CHG"])
        json_df.columns = ["date", "variety_en", "contract", "rank",
                           "trade_company", "trade", "trade_increase",
                           "long_position_company", "long_position", "long_position_increase",
                           "short_position_company", "short_position", "short_position_increase"]

        # for i in json_df.itertuples():
        #     print(i)
        # print(json_df.shape)
        return json_df

    def save_rank_server(self, source_df):
        """ 保存日持仓排名到服务器 """
        self.parser_finished.emit("开始保存上期所{}日持仓排名数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/shfe/rank/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存上期所{}日持仓排名到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)

    @staticmethod
    def get_variety_en(variety_name: str):
        en = VARIETY_EN.get(variety_name.strip(), None)
        if not en:
            logger.error("品种:{} 的交易所代码配置不存在".format(variety_name))
            raise ValueError("上期所品种:{} 的交易所代码配置不存在".format(variety_name))
        return en

    def parser_receipt_source_file(self):
        """ 解析仓单日报源文件 """
        file_path = os.path.join(LOCAL_SPIDER_SRC, "shfe/receipt/{}.json".format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现上期所{}的仓单日报源文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        with open(file_path, "r", encoding="utf-8") as reader:
            source_content = json.load(reader)
        json_df = DataFrame(source_content['o_cursor'])
        # 处理仓库名称
        json_df["WHABBRNAME"] = json_df["WHABBRNAME"].apply(full_width_to_half_width)
        json_df["WHABBRNAME"] = json_df["WHABBRNAME"].apply(lambda name: name.split("$$")[0].strip())
        # 去掉含仓库名称含合计或小计的行
        json_df = json_df[~json_df['WHABBRNAME'].str.contains('总计|小计|合计')]  # 选取品种不含有小计和总计合计的行
        # 处理品种名称
        json_df["VARNAME"] = json_df["VARNAME"].apply(lambda name: name.split("$$")[0].strip())
        # 增加交易代码列
        json_df["VAREN"] = json_df['VARNAME'].apply(self.get_variety_en)
        # 仓单和增减转为int类型
        json_df["WRTWGHTS"] = json_df["WRTWGHTS"].apply(int)
        json_df["WRTCHANGE"] = json_df["WRTCHANGE"].apply(int)
        # 添加日期
        date_str = self.date.strftime("%Y%m%d")
        json_df["DATE"] = [date_str for _ in range(json_df.shape[0])]
        # 整理出想要的数据列(仓库名称(简称),交易代码,日期,仓单,增减)
        result_df = json_df.reindex(columns=["WHABBRNAME", "VAREN", "DATE", "WRTWGHTS", "WRTCHANGE"])
        result_df.columns = ["warehouse", "variety_en", "date", "receipt", "receipt_increase"]
        return result_df

    def save_receipt_server(self, source_df):
        """ 保存仓单日报到服务器 """
        self.parser_finished.emit("开始保存上期所{}仓单日报数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/shfe/receipt/?date=" + self.date.strftime("%Y-%m-%d")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")

        reply = network_manager.post(request, json.dumps(data_body).encode("utf-8"))
        reply.finished.connect(self.save_receipt_server_reply)

    def save_receipt_server_reply(self):
        """ 保存仓单日报到数据库返回 """
        reply = self.sender()
        data = reply.readAll().data()
        reply.deleteLater()
        if reply.error():
            self.parser_finished.emit("保存上期所{}仓单日报到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)
