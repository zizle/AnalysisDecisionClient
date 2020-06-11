# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-09
# ------------------------

"""批量上传大商所的仓库和品种信息"""
import json
import requests
import pandas as pd
from settings import SERVER_ADDR


# 检测仓库编码中是否有重复的简称
def check_fixed_code():
    r = requests.get(SERVER_ADDR + 'house_number/')
    response = json.loads(r.content.decode('utf8'))
    fixed_code_houses = response['warehouses']
    print(fixed_code_houses)
    houses_df = pd.DataFrame(fixed_code_houses)
    duplicate_df = houses_df[houses_df.duplicated(subset=['name'])]
    print(duplicate_df['fixed_code'])


# 检测仓库信息中是否有重复的仓库
def check_exist_warehouse():
    # 请求所有仓库信息
    r = requests.get(url=SERVER_ADDR + 'warehouse/')
    response = json.loads(r.content.decode('utf8'))
    # 检测旧存在的仓库是否有重复的
    exist_warehouses = response['warehouses']
    exist_df = pd.DataFrame(exist_warehouses)
    print(exist_df)
    duplicate_df = exist_df[exist_df.duplicated(subset=['short_name'])]
    print(duplicate_df['fixed_code'])


# 批量添加仓库信息
def add_warehouse():
    file_df = pd.read_excel('./大商所交割信息表.xlsx', sheet_name='大商所交割仓库信息')
    file_df[['经度', '纬度']] = file_df[['经度', '纬度']].apply(lambda x: round(x, 4))
    file_df = file_df.fillna('')
    useful_df = file_df[['地区', '名称', '简称', '地址', '到达站、港', '经度', '纬度']]
    useful_df.columns = ['area', 'name', 'short_name', 'addr', 'arrived', 'longitude', 'latitude']
    # print(useful_df)
    records_dict = useful_df.to_dict(orient='record')
    # print(records_dict)
    # 请求所有仓库信息
    r = requests.get(url=SERVER_ADDR + 'warehouse/')
    response = json.loads(r.content.decode('utf8'))
    # print(response['warehouses'])
    # 检测新添加的仓库是否等于旧仓库（不在旧仓库中的添加进去）
    save_houses = list()
    for to_add_item in records_dict:
        to_save = True
        for exist_item in response['warehouses']:
            if to_add_item['short_name'] == exist_item['short_name']:
                to_save = False
                print('仓库名称重复了-------{}'.format(to_add_item['short_name']))
                print(exist_item['addr'],exist_item['longitude'], exist_item['latitude'])
                print(to_add_item['addr'],to_add_item['longitude'], to_add_item['latitude'])
                print('-----------------------')
        if to_save:
            save_houses.append(to_add_item)
    print('去重已完成!')

    try:
        r = requests.post(
            url=SERVER_ADDR + 'warehouse/',
            headers={'Content-Type': 'application/json;charset=utf8'},
            data=json.dumps({'warehouses': save_houses})
        )
        response = json.loads(r.content.decode('utf8'))
        if r.status_code != 201:
            raise ValueError('错误')
    except Exception as e:
        print(e)
    else:
        print(response['message'])


# 批量添加仓库所涉及的交割品种信息
def delivery_variety_house():
    variety_df = pd.read_excel('./大商所交割信息表.xlsx', sheet_name='大商所交割品种仓库信息')
    useful_df = variety_df[['品种','代码','简称','联系人','联系方式', '升贴水', '仓单单位']]
    useful_df.columns = ['name','name_en', 'short_name','linkman','links', 'premium', 'receipt_unit']

    useful_df = useful_df.fillna('')
    print(useful_df)
    # duplicate_df = useful_df[useful_df.duplicated(subset=['name_en','short_name'])]
    record_dict = useful_df.to_dict(orient='record')
    # print(duplicate_df)
    print(record_dict)

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
    # check_fixed_code()
    # check_exist_warehouse()
    # add_warehouse()
    # delivery_variety_house()
    pass


