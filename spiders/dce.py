# _*_ coding:utf-8 _*_
# @File  : dce
# @Time  : 2020-08-02 14:28
# @Author: zizle
import os
import random
import json
import zipfile
from pandas import DataFrame, read_excel, read_table, merge, concat
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QFile, QUrl
from PyQt5.QtWidgets import qApp
from PyQt5.QtNetwork import QNetworkRequest
from utils.characters import split_number_en
from utils.multipart import generate_multipart_data
from settings import logger
from configs import USER_AGENTS, BASE_DIR, LOCAL_SPIDER_SRC, SERVER


dce_json_path = os.path.join(BASE_DIR, "classini/dce.json")

with open(dce_json_path, "r", encoding="utf-8") as reader:
    GOODS_DICT = json.load(reader)


def get_variety_en(name):
    variety_en = GOODS_DICT.get(name, None)
    if variety_en is None:
        logger.error("大商所{}品种对应的代码不存在...".format(name))
        raise ValueError("品种不存在...")
    return variety_en


def str_to_int(ustring):
    return int(ustring.replace(',', ''))


class DateValueError(Exception):
    """ 日期错误 """


class DCESpider(QObject):
    spider_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(DCESpider, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def get_daily_source_file(self):
        """ 获取日交易源数据xls文件 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`DCESpider`日期.")
        url = "http://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html"
        form_params = {
            "dayQuotes.variety": "all",
            "dayQuotes.trade_type": "0",
            "year": str(self.date.year),
            "month": str(self.date.month - 1),
            "day": self.date.strftime("%d"),
            "exportFlag": "excel"
        }
        form_data = generate_multipart_data(text_dict=form_params)

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.post(request, form_data)
        reply.finished.connect(self.daily_source_file_reply)
        form_data.setParent(reply)

    def daily_source_file_reply(self):
        """ 获取日交易源数据返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'dce/daily/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取大商所{}日交易数据保存到文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_rank_source_file(self):
        """ 获取日持仓排名数据zip源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`DCESpider`日期.")
        url = "http://www.dce.com.cn/publicweb/quotesdata/exportMemberDealPosiQuotesBatchData.html"
        form_params = {
            'memberDealPosiQuotes.variety': 'a',
            'memberDealPosiQuotes.trade_type': '0',
            'year': str(self.date.year),
            'month': str(self.date.month - 1),
            'day': self.date.strftime("%d"),
            'contract.contract_id': 'a2009',
            'contract.variety_id': 'a',
            'batchExportFlag': 'batch'
        }
        form_data = generate_multipart_data(text_dict=form_params)

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.post(request, form_data)
        reply.finished.connect(self.rank_source_file_reply)
        form_data.setParent(reply)

    def rank_source_file_reply(self):
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'dce/rank/{}.zip'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取大商所{}日持仓排名数据源文件成功!".format(self.date.strftime("%Y-%m-%d")), True)


class DCEParser(QObject):
    parser_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(DCEParser, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def parser_daily_source_file(self):
        """ 解析文件数据为DataFrame """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`DCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'dce/daily/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现大商所{}的日交易行情文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        xls_df = read_excel(file_path, thousands=',')
        # 判断表头格式
        if xls_df.columns.values.tolist() != ['商品名称', '交割月份', '开盘价', '最高价', '最低价', '收盘价',
                                              '前结算价', '结算价', '涨跌', '涨跌1', '成交量', '持仓量', '持仓量变化', '成交额']:
            self.parser_finished.emit("{}文件格式有误".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        # 选取无合计,小计,总计的行
        xls_df = xls_df[~xls_df["商品名称"].str.contains("小计|总计|合计")]
        # 交个月份转为int再转为str
        xls_df["交割月份"] = xls_df["交割月份"].apply(lambda x: str(int(x)))
        # 修改商品名称为英文
        xls_df["商品名称"] = xls_df["商品名称"].apply(get_variety_en)
        # 加入日期
        str_date = self.date.strftime("%Y%m%d")
        xls_df["日期"] = [str_date for _ in range(xls_df.shape[0])]
        # 重置列头并重命名
        xls_df = xls_df.reindex(columns=["日期", "商品名称", "交割月份", "前结算价", "开盘价", "最高价", "最低价", "收盘价",
                                         "结算价", "涨跌", "涨跌1", "成交量", "持仓量", "持仓量变化", "成交额"])
        xls_df.columns = ["date", "variety_en", "contract", "pre_settlement", "open_price", "highest", "lowest",
                          "close_price", "settlement", "zd_1", "zd_2", "trade_volume", "empty_volume",
                          "increase_volume", "trade_price"]
        # 合约改为品种+交割月的形式
        xls_df["contract"] = xls_df["variety_en"] + xls_df["contract"]
        self.parser_finished.emit("解析数据文件成功!", False)
        return xls_df

    def save_daily_server(self, source_df):
        """ 保存日行情数据到服务器 """
        self.parser_finished.emit("开始保存大商所{}日交易数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER + "exchange/dce/daily/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存大商所{}日交易数据到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode('utf-8'))
            self.parser_finished.emit(data["message"], True)

    def parser_rank_source_file(self):
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`DCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'dce/rank/{}.zip'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现大商所{}的日持仓排名源文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        # 解压文件的缓存目录
        cache_folder = os.path.join(LOCAL_SPIDER_SRC, 'dce/rank/cache/{}/'.format(self.date.strftime('%Y-%m-%d')))
        # 解压文件到文件夹
        zip_file = zipfile.ZipFile(file_path)
        zip_list = zip_file.namelist()
        for filename in zip_list:
            # filename = filename.encode('cp437').decode('gbk')  # 这样做会无法提取文件。遂修改源代码
            zip_file.extract(filename, cache_folder)  # 循环解压文件到指定目录
        zip_file.close()
        # 取解压后的文件夹下的文件，逐个读取内容解析得到最终的数据集
        return self._parser_variety_rank(cache_folder)

    def save_rank_server(self, source_df):
        """ 保存日持仓排名到服务器 """
        self.parser_finished.emit("开始保存大商所{}日持仓排名数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER + "exchange/dce/rank/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存大商所{}日持仓排名到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)

    @staticmethod
    def _parser_variety_rank(cache_folder):
        """ 读取文件夹内文件解析 """
        all_data_df = DataFrame(columns=["date", "variety_en", "contract", "rank",
                                         "trade_company", "trade", "trade_increase",
                                         "long_position_company", "long_position", "long_position_increase",
                                         "short_position_company", "short_position", "short_position_increase"])

        filename_list = os.listdir(cache_folder)
        for contract_filename in filename_list:
            contract_file_path = os.path.join(cache_folder, contract_filename)
            message_list = contract_filename.split('_')
            c_date = message_list[0]                                  # 得到日期
            contract = message_list[1].upper()                        # 得到合约
            variety_en = split_number_en(message_list[1])[0].upper()  # 得到合约代码
            contract_df = read_table(contract_file_path)
            extract_indexes = list()
            start_index, end_index = None, None
            for df_row in contract_df.itertuples():
                if df_row[1] == "名次":
                    start_index = df_row[0]
                if df_row[1] == "总计":
                    end_index = df_row[0] - 1
                if start_index is not None and end_index is not None:
                    extract_indexes.append([start_index, end_index])
                    start_index, end_index = None, None
            contract_result_df = DataFrame()
            for split_index in extract_indexes:
                target_df = contract_df.loc[split_index[0]:split_index[1]]
                first_row = target_df.iloc[0]
                first_row = first_row.fillna("nana")  # 填充NAN的值为nana方便删除这些列
                target_df.columns = first_row.values.tolist()  # 将第一行作为表头
                target_df = target_df.reset_index()  # 重置索引
                target_df = target_df.drop(labels=0)  # 删除第一行
                if target_df.columns.values.tolist() == ['index', '名次', 'nana', '会员简称', '持买单量', '增减',
                                                         'nana', 'nana', 'nana', 'nana', 'nana']:
                    target_df.columns = ['index2', '名次', 'nana', '会员简称2', '持买单量', 'nana',
                                         '增减2', 'nana', 'nana', 'nana', 'nana']
                elif target_df.columns.values.tolist() == ['index', '名次', 'nana', '会员简称', '持卖单量', '增减',
                                                           'nana', 'nana', 'nana', 'nana', 'nana']:
                    target_df.columns = ['index3', '名次', 'nana', '会员简称3', '持卖单量', 'nana',
                                         '增减3', 'nana', 'nana', 'nana', 'nana']
                # 删除为nana的列
                target_df = target_df.drop("nana", axis=1)  # 删除为nana的列
                if contract_result_df.empty:
                    contract_result_df = target_df
                else:
                    contract_result_df = merge(contract_result_df, target_df, on="名次")
            # 提取需要的列，再重命名列头
            contract_result_df["日期"] = [c_date for _ in range(contract_result_df.shape[0])]
            contract_result_df["品种"] = [variety_en for _ in range(contract_result_df.shape[0])]
            contract_result_df["合约"] = [contract for _ in range(contract_result_df.shape[0])]
            # 重置列名取需要的值
            contract_result_df = contract_result_df.reindex(columns=["日期", "品种", "合约", "名次",
                                                                     "会员简称", "成交量", "增减",
                                                                     "会员简称2", "持买单量", "增减2",
                                                                     "会员简称3", "持卖单量", "增减3"])
            contract_result_df.columns = ["date", "variety_en", "contract", "rank",
                                          "trade_company", "trade", "trade_increase",
                                          "long_position_company", "long_position", "long_position_increase",
                                          "short_position_company", "short_position", "short_position_increase"]
            # 填充缺失值
            contract_result_df[
                ["trade_company", "long_position_company", "short_position_company"]
            ] = contract_result_df[
                ["trade_company", "long_position_company", "short_position_company"]
            ].fillna('')
            contract_result_df = contract_result_df.fillna('0')
            # 修改数据类型
            contract_result_df["rank"] = contract_result_df["rank"].apply(str_to_int)
            contract_result_df["trade"] = contract_result_df["trade"].apply(str_to_int)
            contract_result_df["trade_increase"] = contract_result_df["trade_increase"].apply(str_to_int)
            contract_result_df["long_position"] = contract_result_df["long_position"].apply(str_to_int)
            contract_result_df["long_position_increase"] = contract_result_df["long_position_increase"].apply(
                str_to_int)
            contract_result_df["short_position"] = contract_result_df["short_position"].apply(str_to_int)
            contract_result_df["short_position_increase"] = contract_result_df["short_position_increase"].apply(
                str_to_int)
            # 取1<=名次<=20的数据
            contract_result_df = contract_result_df[
                (1 <= contract_result_df["rank"]) & (contract_result_df["rank"] <= 20)]
            all_data_df = concat([all_data_df, contract_result_df])
        return all_data_df


