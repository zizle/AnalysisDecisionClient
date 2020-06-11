# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-09
# ------------------------

"""批量上传上期所的仓库和品种信息"""
import json
import requests
import pandas as pd
from settings import SERVER_ADDR


def add_warehouse():
    file_df = pd.read_excel('./上期所交割仓单信息表.xlsx', sheet_name='上期所仓库信息')
    file_df[['经度', '纬度']] = file_df[['经度', '纬度']].apply(lambda x: round(x, 4))
    file_df = file_df.fillna('')
    useful_df = file_df[['地区', '名称', '简称', '地址', '到达站、港', '经度', '纬度']]
    useful_df.columns = ['area', 'name', 'short_name', 'addr', 'arrived', 'longitude', 'latitude']
    records_dict = useful_df.to_dict(orient='record')
    try:
        r = requests.post(
            url=SERVER_ADDR + 'warehouse/',
            headers={'Content-Type': 'application/json;charset=utf8'},
            data=json.dumps({'warehouses': records_dict})
        )
        response = json.loads(r.content.decode('utf8'))
        if r.status_code != 201:
            raise ValueError('错误')
    except Exception as e:
        print(e)
    else:
        print(response['message'])


def delivery_variety_house():
    variety_df = pd.read_excel('./上期所交割仓单信息表.xlsx', sheet_name='上期所品种信息')
    useful_df = variety_df[['品种','代码','简称','联系人','联系方式', '升贴水', '仓单单位']]
    useful_df.columns = ['name','name_en', 'short_name','linkman','links', 'premium', 'receipt_unit']

    useful_df = useful_df.fillna('')
    print(useful_df)
    record_dict = useful_df.to_dict(orient='record')
    try:
        r = requests.post(
            url=SERVER_ADDR + 'warehouse/0001/variety/',
            headers={'Content-Type': 'application/json;charset=utf8'},
            data=json.dumps({'variety_record': record_dict})
        )
        response = json.loads(r.content.decode('utf8'))
        if r.status_code != 200:
            raise ValueError('错误')
    except Exception as e:
        print(e)
    else:
        print(response['message'])


if __name__ == '__main__':
    # add_warehouse()
    delivery_variety_house()


