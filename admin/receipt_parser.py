# _*_ coding:utf-8 _*_
# @File  : receipt_parser.py
# @Time  : 2020-09-23 15:01
# @Author: zizle

import os
import json
import pandas as pd
from .receipt_parser_ui import ReceiptParserUI
from utils.constant import VARIETY_EN, VARIETY_ZH
from settings import SERVER_API
from configs import LOCAL_SPIDER_SRC


def get_variety_en(variety_name: str):
    en = VARIETY_EN.get(variety_name.strip(), None)
    if not en:
        print("品种:{}的交易所代码配置不存在".format(variety_name))
        raise ValueError("VARIETY_EN No Exists")
    return en


def get_variety_zh(variety_en: str):
    zh = VARIETY_ZH.get(variety_en, None)
    if not zh:
        print("交易代码:{}中文名称不存在".format(variety_en))
        raise ValueError("VARIETY_ZH No Exists")
    return zh


class ReceiptParser(ReceiptParserUI):
    """ 解析3大交易所的每日仓单数据 进行保存到数据库 """
    def __init__(self, *args, **kwargs):
        super(ReceiptParser, self).__init__(*args, **kwargs)
        self.parser_button.clicked.connect(self.parser_receipts)
        self.warehouse_fixed_code = dict()

    def _get_warehouse_fixed_code(self):
        """ 获取系统中所有的交割仓库对应的fixed_code """


    def parser_receipts(self):
        """ 解析各交易所的数据 """
        shfe_df = self._parser_shfe_receipt()

    def get_fixed_code(self, warehouse_short_name: str):
        """ 通过short_name获取仓库的固定编码 """
        return self.warehouse_fixed_code.get(warehouse_short_name.strip(), '')

    def _parser_shfe_receipt(self):
        """ 解析上期所仓单数据 """
        current_date = self.current_date.text()
        file_path = os.path.join(LOCAL_SPIDER_SRC, "shfe/receipt/{}.json".format(current_date))
        if not os.path.exists(file_path):
            self.message_label.setText("请在【后台管理】-【行业数据】-【交易所数据】获取仓单源文件后再提取")
            return pd.DataFrame()
        with open(file_path, "r", encoding="utf-8") as reader:
            source_content = json.load(reader)
        json_df = pd.DataFrame(source_content['o_cursor'])
        # 处理仓库名称
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

        for row in json_df.itertuples():
            print(row)


    def _parser_czce_receipt(self):
        """ 解析郑商所仓单数据 """

    def _parser_dce_receipt(self):
        """ 解析大商所仓单数据 """


