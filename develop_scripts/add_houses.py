# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-01
# ------------------------


import json
import requests
import pandas as pd
from settings import SERVER_ADDR


"""批量上传仓库编号数据"""
def many_house_number():
    house_df = pd.read_excel('./品种交割仓库编号及信息表.xlsx', sheet_name='仓库编号表')
    house_df = house_df.drop_duplicates(subset=['仓库名称','编号'])
    house_df['编号'] = house_df['编号'].apply(lambda x: "%04d" %x)
    try:
        r = requests.post(
            url=SERVER_ADDR + 'house_number/',
            headers={'Content-Type':'application/json;charset=utf8'},
            data=json.dumps({'houses': house_df.values.tolist()})
        )
        response = json.loads(r.content.decode('utf8'))
        if r.status_code != 201:
            raise ValueError('错误')
    except Exception as e:
        print(e)
    else:
        print(response['message'])

"""批量上传仓库信息数据"""
def add_houses_message():
    houses_df = pd.read_excel('./品种交割仓库编号及信息表.xlsx', sheet_name='郑商所仓库信息表')
    houses_df = houses_df.drop_duplicates(subset=['编号'], keep='first')
    houses_df[['经度','纬度']] = houses_df[['经度','纬度']].apply(lambda x: round(x, 4))
    houses_df = houses_df.fillna('')

    useful_df = houses_df[['地区', '全称', '简称', '地址','到达站、港', '经度', '纬度']]
    useful_df.columns = ['area','name','short_name','addr','arrived','longitude','latitude']
    # print(useful_df)
    records_dict = useful_df.to_dict(orient='records')
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


"""批量上传仓库的交割品种信息"""


def delivery_variety_house():
    variety_df = pd.read_excel('./品种交割仓库编号及信息表.xlsx', sheet_name='郑商所品种信息表')
    useful_df = variety_df[['品种','代码','简称','联系人','联系方式','升贴水','仓单单位']]
    useful_df.columns = ['name','name_en', 'short_name','linkman','links','premium','receipt_unit']
    print(useful_df)
    useful_df = useful_df.fillna('')
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
    # many_house_number()
    # add_houses_message()
    delivery_variety_house()


