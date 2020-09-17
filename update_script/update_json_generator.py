# _*_ coding:utf-8 _*_
# @File  : update_json_generator
# @Time  : 2020-08-02 22:15
# @Author: zizle

"""
生成版本更新配置文件
使用方法：
Terminal: python update_json_generator.py SysBit Version ClientPath
SysBit-系统位数,如32, 64
Version-当前版本号,如0.0.1
ClientPath-文件绝对路径,如d:\client64\
"""

import os
import sys
import json
from hashlib import md5


def get_file_md5(file_path):
    """ 获取文件的md5值"""
    if not os.path.isfile(file_path):
        return ''
    encrypt = md5()
    f = open(file_path, "rb")
    while True:
        b = f.read(8192)
        if not b:
            break
        encrypt.update(b)
    f.close()
    return encrypt.hexdigest()


def fill_update_dict(root_path, replace_path):
    """ 查找文件并填充文件对应md5字典 """
    files_list = os.listdir(root_path)
    for filename in files_list:
        temp_path = os.path.join(root_path, filename)
        if os.path.isdir(temp_path):  # 还是文件夹
            fill_update_dict(temp_path, replace_path)
        else:
            file_md5 = get_file_md5(temp_path)
            file_key = temp_path.replace(replace_path, '')
            file_key = '/'.join(file_key.split('\\'))
            UPDATE_DICT[file_key] = file_md5


if __name__ == '__main__':
    UPDATE_DICT = dict()          # 待更新的文件字典
    PLATEFORM = str(sys.argv[1])  # 操作系统WIN7 WIN10
    SYS_BIT = str(sys.argv[2])    # 系统位数(后台客户端使用admin)
    VERSION = str(sys.argv[3])    # 版本号
    FILES_DIR = str(sys.argv[4])  # 客户端文件夹路径
    fill_update_dict(FILES_DIR, FILES_DIR)
    update_json = {
        "VERSION": VERSION,
        "SERVER": "http://210.13.218.130:9004/static/UPDATE/INSIDE/",
        "FILES": UPDATE_DICT
    }
    update_filename = "update_{}_{}.json".format(PLATEFORM, SYS_BIT)
    with open(update_filename, "w", encoding="utf-8") as f:
        json.dump(update_json, f, indent=4, ensure_ascii=False)
