# _*_ coding:utf-8 _*_
# @File  : receipt_parser.py
# @Time  : 2020-09-23 15:01
# @Author: zizle

import re
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QBrush, QColor
from .receipt_parser_ui import ReceiptParserUI
from utils.client import get_user_token
from utils.constant import VARIETY_EN, VARIETY_ZH
from utils.characters import full_width_to_half_width, split_zh_en
from settings import SERVER_API,logger
from configs import LOCAL_SPIDER_SRC


def get_variety_en(variety_name: str):
    en = VARIETY_EN.get(variety_name.strip(), None)
    if not en:
        print("品种:{} 的交易所代码配置不存在".format(variety_name))
        raise ValueError("VARIETY_EN No Exists")
    return en


def get_variety_zh(variety_en: str):
    zh = VARIETY_ZH.get(variety_en, None)
    if not zh:
        print("交易代码:{} 中文名称不存在".format(variety_en))
        raise ValueError("VARIETY_ZH No Exists")
    return zh


class ReceiptParser(ReceiptParserUI):
    """ 解析3大交易所的每日仓单数据 进行保存到数据库 """
    def __init__(self, *args, **kwargs):
        super(ReceiptParser, self).__init__(*args, **kwargs)
        self.parser_button.clicked.connect(self.parser_receipts)
        self.warehouse_fixed_code = dict()
        self.current_exchange = ''  # 当前解析的交易所,用于记录日志
        self.is_ready_saving = False
        self.sources = None
        self._get_warehouse_fixed_code()

        self.commit_button.clicked.connect(self.save_receipt_to_server)

    def _get_warehouse_fixed_code(self):
        """ 获取系统中所有的交割仓库对应的fixed_code """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'warehouse-number/'
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.warehouse_fixed_code_reply)

    def warehouse_fixed_code_reply(self):
        """ 仓库编码信息返回 """
        reply = self.sender()
        if reply.error():
            logger.error("提取仓单信息前获取仓库编码失败了:{}".format(reply.error()))
        else:
            data = json.loads(reply.readAll().data().decode('utf-8'))
            warehouses = data["warehouses"]
            self.warehouse_fixed_code.clear()
            for warehouse_item in warehouses:
                self.warehouse_fixed_code[warehouse_item["name"]] = warehouse_item["fixed_code"]

    def get_warehouse_code(self, warehouse_name: str):
        """ 获取仓库的固定编码 """
        fixed_code = self.warehouse_fixed_code.get(warehouse_name.strip(), None)
        if fixed_code is None:
            logger.error("{} 仓库: {} 的固定编码在系统中不存在,需要新增!!!".format(self.current_exchange, warehouse_name))
            return ''
        else:
            return fixed_code

    def parser_receipts(self):
        """ 解析各交易所的数据 """
        self.sources = None
        column_indexes = ["fixed_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]
        result_df = pd.DataFrame(columns=column_indexes)
        shfe_df = self._parser_shfe_receipt()
        czce_df = self._parser_czce_receipt()
        dce_df = self._parser_dce_receipt()
        result_df = pd.concat([result_df, shfe_df, czce_df, dce_df])
        # 修改表头fixed_code 为warehouse_code与后端对应
        result_df.columns = ["warehouse_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]
        source_values = result_df.to_dict(orient="records")
        # 将数据在预览表格中显示
        self.preview_table_values(source_values)

    def preview_table_values(self, source_values):
        """ 预览表格显示数据 """
        self.preview_table.clearContents()
        self.preview_table.setRowCount(len(source_values))
        for row, row_item in enumerate(source_values):
            item0 = QTableWidgetItem(row_item["warehouse_code"])
            item0.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["warehouse_name"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["variety"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["variety_en"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(row_item["date"])
            item4.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 4, item4)

            item5 = QTableWidgetItem(str(row_item["receipt"]))
            item5.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 5, item5)

            item6 = QTableWidgetItem(str(row_item["increase"]))
            item6.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 6, item6)

            if not row_item["warehouse_code"]:
                item0.setForeground(QBrush(QColor(255, 255, 255)))
                item0.setBackground(QBrush(QColor(66, 66, 233)))
                item1.setForeground(QBrush(QColor(255, 255, 255)))
                item1.setBackground(QBrush(QColor(66, 66, 233)))
                item2.setForeground(QBrush(QColor(255, 255, 255)))
                item2.setBackground(QBrush(QColor(66, 66, 233)))
                item3.setForeground(QBrush(QColor(255, 255, 255)))
                item3.setBackground(QBrush(QColor(66, 66, 233)))
                item4.setForeground(QBrush(QColor(255, 255, 255)))
                item4.setBackground(QBrush(QColor(66, 66, 233)))
                item5.setForeground(QBrush(QColor(255, 255, 255)))
                item5.setBackground(QBrush(QColor(66, 66, 233)))
                item6.setForeground(QBrush(QColor(255, 255, 255)))
                item6.setBackground(QBrush(QColor(66, 66, 233)))
        if not self.is_ready_saving:
            self.message_label.setText("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取后保存")
        else:
            self.sources = source_values

    def save_receipt_to_server(self):
        """ 将数据保存到数据库 """
        if self.sources is None:
            self.message_label.setText("请先解析提取预览数据!")
            return
        # 保存数据请求
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "delivery/receipt/"
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("Utf-8"), user_token.encode("utf-8"))
        reply = network_manager.post(request, json.dumps(self.sources).encode("utf-8"))
        reply.finished.connect(self.save_receipt_reply)

    def save_receipt_reply(self):
        """ 保存仓单请求返回 """
        reply = self.sender()
        if reply.error():
            self.message_label.setText("保存仓单数据失败:{}".format(reply.error()))
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.message_label.setText("保存成功新增数据{}个!".format(data["save_count"]))
            self.preview_table.clearContents()  # 清空数据
            self.preview_table.setRowCount(0)
        reply.deleteLater()

    def _parser_shfe_receipt(self):
        """ 解析上期所仓单数据 """
        self.current_exchange = "上海期货交易所"
        current_date = self.current_date.text()
        file_path = os.path.join(LOCAL_SPIDER_SRC, "shfe/receipt/{}.json".format(current_date))
        if not os.path.exists(file_path):
            self.message_label.setText("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取")
            self.is_ready_saving = False
            return pd.DataFrame()
        self.message_label.setText("提取上海期货交易所仓单数据...")
        with open(file_path, "r", encoding="utf-8") as reader:
            source_content = json.load(reader)
        json_df = pd.DataFrame(source_content['o_cursor'])
        # 处理仓库名称
        json_df["WHABBRNAME"] = json_df["WHABBRNAME"].apply(full_width_to_half_width)
        json_df["WHABBRNAME"] = json_df["WHABBRNAME"].apply(lambda name: name.split("$$")[0].strip())
        # 去掉含仓库名称含合计或小计的行
        json_df = json_df[~json_df['WHABBRNAME'].str.contains('总计|小计|合计')]  # 选取品种不含有小计和总计合计的行
        # 处理品种名称
        json_df["VARNAME"] = json_df["VARNAME"].apply(lambda name: name.split("$$")[0].strip())
        # 增加交易代码列
        json_df["VAREN"] = json_df['VARNAME'].apply(get_variety_en)
        # 增加中文品种列
        json_df["VARZHCN"] = json_df['VAREN'].apply(get_variety_zh)
        # 仓单和增减转为int类型
        json_df["WRTWGHTS"] = json_df["WRTWGHTS"].apply(int)
        json_df["WRTCHANGE"] = json_df["WRTCHANGE"].apply(int)
        # 添加仓库的系统编码
        json_df["FIXEDCODE"] = json_df["WHABBRNAME"].apply(self.get_warehouse_code)
        # 添加日期
        date_str = datetime.strptime(self.current_date.text(), "%Y-%m-%d").strftime("%Y%m%d")
        json_df["DATE"] = [date_str for _ in range(json_df.shape[0])]
        # 整理出想要的数据列(仓库编码,仓库名称(简称),品种中文,交易代码,日期,仓单,增减)
        result_df = json_df.reindex(columns=["FIXEDCODE", "WHABBRNAME", "VARZHCN", "VAREN", "DATE", "WRTWGHTS", "WRTCHANGE"])
        result_df.columns = ["fixed_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]
        self.message_label.setText("提取上海期货交易所仓单数据结束!")
        return result_df

    def _parser_czce_receipt(self):
        """ 解析郑商所仓单数据 """
        self.current_exchange = "郑州商品交易所"
        current_date = self.current_date.text()
        file_path = os.path.join(LOCAL_SPIDER_SRC, "czce/receipt/{}.xls".format(current_date))
        if not os.path.exists(file_path):
            self.message_label.setText("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取")
            self.is_ready_saving = False
            return pd.DataFrame()
        self.message_label.setText("提取郑州商品交易所仓单数据...")
        xls_df = pd.read_excel(file_path)
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
        column_indexes = ["fixed_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]

        result_df = pd.DataFrame(columns=column_indexes)
        for variety_en in variety_dict:
            data_index_range = variety_index_dict[variety_en]  # 数据在dataFrame中的起终索引
            variety_df = xls_df.iloc[data_index_range[0]:data_index_range[1] + 1, :]
            variety_df = self._parser_receipt_sub_df(variety_en, variety_df)
            result_df = pd.concat([result_df, variety_df])
        self.message_label.setText("提取郑州商品交易所仓单数据结束.")
        return result_df

    def _parser_receipt_sub_df(self, variety_en, variety_df):
        """ 解析郑商所每个品种的仓单日报 """
        # 20200220后的数据强筋小麦为机构简称和机构编号，仓单为‘确认书数量’
        variety_df.columns = variety_df.iloc[0].replace('机构编号',
                                                        '仓库编号').replace('机构简称',
                                                                        '仓库简称').replace('厂库编号',
                                                                                        '仓库编号').replace('厂库简称',
                                                                                                        '仓库简称').replace(
            '仓单数量(完税)',
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
        result_df = pd.DataFrame()
        result_df['仓单数量'] = variety_df['仓单数量'].groupby(variety_df['仓库简称']).sum()  # 计算和
        result_df['当日增减'] = variety_df['当日增减'].groupby(variety_df['仓库简称']).sum()
        result_df.reset_index()
        wh_name = variety_df[['仓库简称', '升贴水']].drop_duplicates(subset='仓库简称', keep='first')
        result_df = pd.merge(wh_name, result_df, on='仓库简称')
        result_df['品种代码'] = [variety_en for _ in range(result_df.shape[0])]
        # 将仓库简称的字符转为半角
        result_df["仓库简称"] = result_df["仓库简称"].apply(full_width_to_half_width)
        # 增加品种中文名称,仓库固定编码,日期
        result_df['品种名称'] = result_df["品种代码"].apply(get_variety_zh)
        result_df['仓库编号'] = result_df["仓库简称"].apply(self.get_warehouse_code)
        str_date = datetime.strptime(self.current_date.text(), "%Y-%m-%d").strftime("%Y%m%d")
        result_df["日期"] = [str_date for _ in range(result_df.shape[0])]

        result_df = result_df.reindex(columns=["仓库编号", "仓库简称", "品种名称", "品种代码", "日期", "仓单数量", "当日增减"])
        result_df.columns = ["fixed_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]
        return result_df

    def _parser_dce_receipt(self):
        """ 解析大商所仓单数据 """
        self.message_label.setText("提取大连商品交易所仓单数据...")
        self.current_exchange = "大连商品交易所"
        current_date = self.current_date.text()
        file_path = os.path.join(LOCAL_SPIDER_SRC, "dce/receipt/{}.html".format(current_date))
        if not os.path.exists(file_path):
            self.message_label.setText("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取")
            self.is_ready_saving = False
            return pd.DataFrame()
        html_df = pd.read_html(file_path, encoding='utf-8')[0]
        if html_df.columns.values.tolist() != ['品种', '仓库/分库', '昨日仓单量', '今日仓单量', '增减']:
            logger.error("郑商所的数据格式出现错误,解析失败!")
            return pd.DataFrame()
        # 修改列头
        html_df.columns = ["VARIETY", "WARENAME", "YRECEIPT", "TRECEIPT", "INCREATE"]
        # 填充nan为上一行数据
        html_df.fillna(method='ffill', inplace=True)
        # 去除品种含小计,总计等行
        html_df = html_df[~html_df['VARIETY'].str.contains('总计|小计|合计')]
        # 仓库简称处理
        html_df["WARENAME"] = html_df["WARENAME"].apply(full_width_to_half_width)
        html_df["FIXEDCODE"] = html_df["WARENAME"].apply(self.get_warehouse_code)  # 新增仓库编号
        # 增加品种代码
        html_df["VARIETYEN"] = html_df["VARIETY"].apply(get_variety_en)
        # 增加今日时间
        date_str = datetime.strptime(self.current_date.text(), "%Y-%m-%d").strftime("%Y%m%d")
        html_df["DATE"] = [date_str for _ in range(html_df.shape[0])]
        # 重置索引
        result_df = html_df.reindex(columns=["FIXEDCODE", "WARENAME", "VARIETY", "VARIETYEN", "DATE", "TRECEIPT", "INCREATE"])
        result_df.columns = ["fixed_code", "warehouse_name", "variety", "variety_en", "date", "receipt", "increase"]
        self.is_ready_saving = True  # 准备保存(因为大商所是最后一个解析的交易所)
        self.message_label.setText("提取所有交易所{}仓单数据完成!(蓝行为新仓库)".format(self.current_date.text()))
        return result_df
