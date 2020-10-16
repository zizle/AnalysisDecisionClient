# _*_ coding:utf-8 _*_
# @File  : czce.py
# @Time  : 2020-07-23 9:36
# @Author: zizle
import os
import re
import json
import random
import numpy as np
from pandas import read_excel, DataFrame, concat, merge
from datetime import datetime
from PyQt5.QtWidgets import qApp
from PyQt5.QtCore import QFile, pyqtSignal, QObject, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from settings import LOCAL_SPIDER_SRC, SERVER_API, USER_AGENTS
from utils.characters import full_width_to_half_width, split_zh_en, split_number_en


# 将品种月份修改为品种+4位合约的形式
def modify_contract_express(contract, current_date):
    number_en = split_number_en(contract)
    return current_date[2].join(number_en)


class DateValueError(Exception):
    """ 日期错误 """


class CZCESpider(QObject):
    spider_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(CZCESpider, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def get_daily_source_file(self):
        """ 获取日交易数据源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCESpider`日期.")
        url = "http://www.czce.com.cn/cn/DFSStaticFiles/Future/{}/{}/FutureDataDaily.xls".format(self.date.year, self.date.strftime('%Y%m%d'))
        network_manager = getattr(qApp, "_network")
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.daily_source_file_reply)

    def daily_source_file_reply(self):
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/daily/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取郑商所{}日交易数据源文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_rank_source_file(self):
        """ 获取日持仓排名数据源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCESpider`日期.")
        url = "http://www.czce.com.cn/cn/DFSStaticFiles/Future/{}/{}/FutureDataHolding.xls".format(self.date.year, self.date.strftime('%Y%m%d'))

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.rank_source_file_reply)

    def rank_source_file_reply(self):
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/rank/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取郑商所{}日持仓排名数据源文件成功!".format(self.date.strftime("%Y-%m-%d")), True)

    def get_receipt_source_file(self):
        """ 获取仓单日报数据源文件保存至本地 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCESpider`日期.")
        url = "http://www.czce.com.cn/cn/DFSStaticFiles/Future/{}/{}/FutureDataWhsheet.xls".format(self.date.year, self.date.strftime('%Y%m%d'))

        network_manager = getattr(qApp, "_network")

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, random.choice(USER_AGENTS))
        reply = network_manager.get(request)
        reply.finished.connect(self.receipt_source_file_reply)

    def receipt_source_file_reply(self):
        """ 获取仓单日报返回 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.spider_finished.emit("失败:" + str(reply.error()), True)
            return
        save_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/receipt/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        file_data = reply.readAll()
        file_obj = QFile(save_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        reply.deleteLater()
        self.spider_finished.emit("获取郑商所{}仓单日报数据源文件成功!".format(self.date.strftime("%Y-%m-%d")), True)


class CZCEParser(QObject):
    parser_finished = pyqtSignal(str, bool)

    def __init__(self, *args, **kwargs):
        super(CZCEParser, self).__init__(*args, **kwargs)
        self.date = None

    def set_date(self, date):
        self.date = datetime.strptime(date, '%Y-%m-%d')

    def parser_daily_source_file(self):
        """ 解析源文件数据为pandas的DataFrame """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/daily/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现郑商所{}的日交易行情文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        # 使用pandas解析数据
        xls_df = read_excel(file_path, thousands=',', skiprows=[0])
        # xls_df.columns = xls_df.iloc[0]  # 第一行作为列头
        # xls_df = xls_df.drop(xls_df.index[0])  # 删除第一行
        xls_df = xls_df[~xls_df['品种月份'].str.contains('总计|小计')]  # 选取品种月份不含有小计和总计的行
        xls_df['品种代码'] = xls_df['品种月份'].apply(lambda x: x[:2])  # 变为品种
        # 2020-09-07 空盘量->持仓量
        if xls_df.columns.values.tolist() != [
            '品种月份', '昨结算', '今开盘', '最高价', '最低价', '今收盘', '今结算', '涨跌1', '涨跌2', '成交量(手)', '持仓量', '增减量', '成交额(万元)', '交割结算价', '品种代码'
        ]:
            self.parser_finished.emit("源数据文件格式有误,解析失败!", True)
            return DataFrame()
        data_date = self.date.strftime('%Y%m%d')
        xls_df['日期'] = [data_date for _ in range(xls_df.shape[0])]
        xls_df = xls_df.fillna(0)
        xls_df.columns = [
            "contract", "pre_settlement", "open_price", "highest", "lowest", "close_price", "settlement", "zd_1", "zd_2",
            "trade_volume", "empty_volume", "increase_volume", "trade_price", "delivery_price", "variety_en", "date",
        ]
        # 将品种月份处理为4位合约(分离字母数字后插入年份的第3个数)
        xls_df["contract"] = xls_df["contract"].apply(modify_contract_express, args=(data_date,))
        self.parser_finished.emit("解析数据文件成功!", False)
        return xls_df

    def save_daily_server(self, source_df):
        """ 保存日行情数据到服务器 """
        self.parser_finished.emit("开始保存郑商所{}日交易数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/czce/daily/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存郑商所{}日交易数据到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode('utf-8'))
            self.parser_finished.emit(data["message"], True)

    def parser_rank_source_file(self):
        """ 解析日持仓排名数据源文件 """
        if self.date is None:
            raise DateValueError("请先使用`set_date`设置`CZCEParser`日期.")
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/rank/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现郑商所{}的日持仓排名源文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        # 读取文件
        xls_df = read_excel(file_path, thousands=',')
        variety_index_dict = dict()  # 存品种的起始终止行
        contract_index_dict = dict()  # 存合约的起始终止行
        variety_dict = dict()  # 存品种的dict
        contract_set = set()  # 存合约的dict
        variety_en = None
        contract_en = None
        is_variety = True
        # 遍历每一行，取出每个品种的数据表
        for row_content in xls_df.itertuples():
            info_for_match_ = full_width_to_half_width(row_content[1])
            search_variety = re.search(r'品种:(.*)\s日期.*', info_for_match_)  # 找到品种行开头
            search_contract = re.search(r'合约:(.*)\s日期.*', info_for_match_)  # 找到合约
            search_sum = re.search(r'合计', info_for_match_)
            if search_variety:  # 如果找到品种记录下品种和开始行
                zh_en_variety = search_variety.group(1)
                variety_name, variety_en = split_zh_en(zh_en_variety)
                if variety_en == "PTA":
                    variety_en = "TA"
                variety_dict[variety_en] = variety_name
                variety_index_dict[variety_en] = [row_content[0] + 1]
                is_variety = True
            elif search_contract:  # 如果找到合约,从品种数据去品种中文名,记录下开始行
                contract_en = search_contract.group(1)
                contract_set.add(contract_en)
                contract_index_dict[contract_en] = [row_content[0] + 1]
                is_variety = False
            else:
                pass  # 无则继续
            if search_sum and (variety_en or contract_en):  # 如果找到合计行，记录下当前品种的结束行
                if is_variety:

                    variety_index_dict[variety_en].append(row_content[0])
                else:
                    contract_index_dict[contract_en].append(row_content[0])
            else:
                pass  # 无则继续
        # 整理数据
        column_indexes = ['variety_en', 'contract', 'rank',
                          'trade_company', 'trade', 'trade_increase',
                          'long_position_company', 'long_position', 'long_position_increase',
                          'short_position_company', 'short_position', 'short_position_increase']

        result_df = DataFrame(columns=column_indexes)
        str_date = self.date.strftime("%Y%m%d")
        # 每个品种数据框
        for variety_en in variety_dict:
            variety_index_range = variety_index_dict[variety_en]
            variety_df = xls_df.iloc[variety_index_range[0]:variety_index_range[1] + 1, :]
            variety_df = self._parser_rank_sub_df(variety_name=variety_dict[variety_en], sub_df=variety_df)
            # 填充品种代码和合约的值
            variety_df["variety_en"] = [variety_en for _ in range(variety_df.shape[0])]
            variety_df["contract"] = [variety_en for _ in range(variety_df.shape[0])]
            # print(variety_en, "\n", variety_df)
            result_df = concat([result_df, variety_df])
        # 每个合约数据框
        for contract in contract_set:
            contract_index_range = contract_index_dict[contract]
            # variety_key = 'PTA' if contract[:2] == 'TA' else contract[:2]
            variety_key = contract[:2]
            # print(variety_dict[variety_key], contract, contract_index_range)
            contract_df = xls_df.iloc[contract_index_range[0]:contract_index_range[1] + 1, :]
            contract_df = self._parser_rank_sub_df(variety_name=variety_dict[variety_key], sub_df=contract_df)
            # 填充品种代码和合约的值
            contract_df["variety_en"] = [variety_key for _ in range(contract_df.shape[0])]
            target_contract = modify_contract_express(contract.strip(), str_date)
            contract_df["contract"] = [target_contract for _ in range(contract_df.shape[0])]
            # print(contract, "\n", contract_df)
            result_df = concat([result_df, contract_df])
        str_date = self.date.strftime("%Y%m%d")
        result_df["date"] = [str_date for _ in range(result_df.shape[0])]
        return result_df

    def _parser_rank_sub_df(self, variety_name, sub_df):
        """ 解析每个品种或合约的数据框 """
        column_indexes = sub_df.iloc[0].values.tolist()
        # print(column_indexes)
        if column_indexes != ['名次', '会员简称', '成交量（手）', '增减量', '会员简称', '持买仓量', '增减量', '会员简称', '持卖仓量', '增减量']:
            raise ValueError("{}郑商所的'{}'持仓排名数据表头格式有误!".format(self.date.strftime("%Y-%m-%d"), variety_name))
        column_indexes = ['名次', '成交会员', '成交量', '成交增减', '买仓会员', '买仓量', '买仓增减', '卖仓会员', '卖仓量', '卖仓增减']
        sub_df.columns = column_indexes
        # sub_df = sub_df.reindex(columns=column_indexes)  # 重新调整列
        sub_df = sub_df.drop(sub_df.index[0])  # 删除第一行
        # 去除合计行
        sub_df = sub_df[~sub_df['名次'].str.contains('合计')]  # 选取不含有合计的行
        sub_df[['名次', '成交量', '成交增减', '买仓量', '买仓增减', '卖仓量', '卖仓增减']] = sub_df[['名次', '成交量', '成交增减', '买仓量', '买仓增减', '卖仓量', '卖仓增减']].replace('-', 0).astype(int)
        # 增加品种代码、合约两列
        new_column_indexes = ["品种代码", "合约"] + column_indexes

        sub_df = sub_df.reindex(columns=new_column_indexes)
        reset_indexes = ['variety_en', 'contract', 'rank',
                         'trade_company', 'trade', 'trade_increase',
                         'long_position_company', 'long_position', 'long_position_increase',
                         'short_position_company', 'short_position', 'short_position_increase']
        sub_df.columns = reset_indexes  # 修改列名
        return sub_df

    def save_rank_server(self, source_df):
        """ 保存日持仓排名到服务器 """
        self.parser_finished.emit("开始保存郑商所{}日持仓排名数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/czce/rank/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存郑商所{}日持仓排名到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)

    def parser_receipt_source_file(self):
        """ 解析仓单日报源文件 """
        file_path = os.path.join(LOCAL_SPIDER_SRC, 'czce/receipt/{}.xls'.format(self.date.strftime("%Y-%m-%d")))
        if not os.path.exists(file_path):
            self.parser_finished.emit("没有发现郑商所{}的仓单日报源文件,请先抓取数据!".format(self.date.strftime("%Y-%m-%d")), True)
            return DataFrame()
        # 读取文件
        xls_df = read_excel(file_path)
        xls_df = xls_df.fillna('')
        variety_index_dict = dict()
        variety_dict = dict()
        variety_en = None  # 品种标记
        pre_variety_en = None
        for row_content in xls_df.itertuples():
            info_for_match_ = full_width_to_half_width(row_content[1])
            search_v = re.search(r'品种:(.*)\s单位.*', info_for_match_)  # 品种
            total_count = re.search(r'总计', info_for_match_)
            if search_v:  # 取得品种和品种的英文代码
                pre_variety_en = variety_en
                has_new_variety = True
                zh_en_variety = search_v.group(1)
                variety_name, variety_en = split_zh_en(zh_en_variety)
                if variety_en == "PTA":
                    variety_en = "TA"
                variety_dict[variety_en] = variety_name
                variety_index_dict[variety_en] = [row_content[0] + 1]
            else:
                has_new_variety = False
            # 获取当前品种的数据表
            if total_count and variety_en:
                variety_index_dict[variety_en].append(row_content[0])
            # 当没有总计时有上一个品种记录且找到了新品种，那么老品种结束行应该是找到新品种行的上一行
            if not total_count and pre_variety_en and has_new_variety:  # 补充没有总计时无法添加结束行的问题，该问题与20191111日后的数据出现
                variety_index_dict[pre_variety_en].append(row_content[0] - 1)

        # 整理数据
        column_indexes = ['variety_en', 'warehouse', 'receipt', 'receipt_increase', 'premium_discount']

        result_df = DataFrame(columns=column_indexes)
        for variety_en in variety_dict:
            data_index_range = variety_index_dict[variety_en]  # 数据在dataFrame中的起终索引
            variety_df = xls_df.iloc[data_index_range[0]:data_index_range[1] + 1, :]
            variety_df = self._parser_receipt_sub_df(variety_en, variety_df)
            result_df = concat([result_df, variety_df])
        str_date = self.date.strftime("%Y%m%d")
        result_df["date"] = [str_date for _ in range(result_df.shape[0])]
        return result_df

    @staticmethod
    def _parser_receipt_sub_df(variety_en, variety_df):
        """ 解析每个品种的仓单日报 """
        # 20200220后的数据强筋小麦为机构简称和机构编号，仓单为‘确认书数量’
        variety_df.columns = variety_df.iloc[0].replace('机构编号',
                                                        '仓库编号').replace('机构简称',
                                                                        '仓库简称').replace('厂库编号',
                                                                                        '仓库编号').replace('厂库简称',
                                                                                                        '仓库简称').replace('仓单数量(完税)',
                                                                                                                        '仓单数量').replace('确认书数量', '仓单数量')  # 以第一行为列头
        variety_df = variety_df.drop(variety_df.index[0])  # 删除第一行
        variety_df = variety_df[~variety_df['仓库编号'].str.contains('总计|小计')]  # 选取不含有小计和总计的行
        # 把仓库简称的列空置替换为NAN，并使用前一个进行填充
        variety_df['仓库编号'] = variety_df['仓库编号'].replace('', np.nan).fillna(method='ffill')
        variety_df['仓库简称'] = variety_df['仓库简称'].replace('', np.nan).fillna(method='ffill')
        variety_df['仓单数量'] = variety_df['仓单数量'].replace('', np.nan).fillna(0)

        # 目标数据样式
        # 代码      仓库      仓单      增减      升贴水
        # CF        河南国储   20       0        ''

        if '升贴水' not in variety_df.columns:
            variety_df['升贴水'] = [0 for _ in range(variety_df.shape[0])]
        variety_df['升贴水'] = variety_df['升贴水'].replace('-', 0)
        # 将仓单数量列转为int
        variety_df['仓单数量'] = variety_df['仓单数量'].apply(lambda x: int(x))  # 转为int计算
        variety_df['当日增减'] = variety_df['当日增减'].apply(lambda x: int(x))
        result_df = DataFrame()
        result_df['仓单数量'] = variety_df['仓单数量'].groupby(variety_df['仓库简称']).sum()  # 计算和
        result_df['当日增减'] = variety_df['当日增减'].groupby(variety_df['仓库简称']).sum()
        result_df.reset_index()
        wh_name = variety_df[['仓库简称', '升贴水']].drop_duplicates(subset='仓库简称', keep='first')
        result_df = merge(wh_name, result_df, on='仓库简称')
        result_df['品种代码'] = [variety_en for _ in range(result_df.shape[0])]
        result_df = result_df.reindex(columns=["品种代码", "仓库简称", "仓单数量", "当日增减", "升贴水"])

        result_df.columns = ['variety_en', 'warehouse', 'receipt', 'receipt_increase', 'premium_discount']  # 修改列名
        return result_df

    def save_receipt_server(self, source_df):
        """ 保存仓单日报到服务器 """
        self.parser_finished.emit("开始保存郑商所{}仓单日报数据到服务器数据库...".format(self.date.strftime("%Y-%m-%d")), False)
        data_body = source_df.to_dict(orient="records")
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "exchange/czce/receipt/?date=" + self.date.strftime("%Y-%m-%d")
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
            self.parser_finished.emit("保存郑商所{}仓单日报到服务数据库失败:\n{}".format(self.date.strftime("%Y-%m-%d"), reply.error()), True)
        else:
            data = json.loads(data.decode("utf-8"))
            self.parser_finished.emit(data["message"], True)
