# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-16
# ------------------------

"""添加品种交割信息(最后交易日、交割单位、仓单有效期)"""
import json
import requests
import pandas as pd
from settings import SERVER_ADDR


def get_file_content():
    source_df = pd.read_excel('./品种交割信息.xlsx')
    useful_df = source_df[['名称', '英文代号', '最后交易日', '交割月投机限仓', '仓单有效期', '最小交割单位']]

    useful_df.columns = ['variety','variety_en','last_trade', 'limit_holding','receipt_expire','delivery_unit']
    useful_df = useful_df.fillna('')
    records_dict = useful_df.to_dict(orient='records')
    print(records_dict)
    try:
        r = requests.post(
            url=SERVER_ADDR + 'delivery/variety-message/',
            headers={'Content-Type': 'application/json;charset=utf8'},
            data=json.dumps({'variety_record': records_dict})
        )
        response = json.loads(r.content.decode('utf8'))
        if r.status_code != 200:
            raise ValueError('错误')
    except Exception as e:
        print(e)
    else:
        print(response['message'])


if __name__ == '__main__':
    get_file_content()