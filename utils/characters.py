# _*_ coding:utf-8 _*_
# @File  : characters.py
# @Time  : 2020-07-20 13:35
# @Author: zizle
from itertools import groupby

def full_width_to_half_width(ustring):
    """ 全角转半角 """
    reverse_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:  # 全角空格直接转换
            inside_code = 32
        elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
            inside_code -= 65248
        else:
            pass
        reverse_str += chr(inside_code)
    return reverse_str


def half_width_to_full_width(ustring):
    """半角转全角"""
    reverse_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:  # 半角空格直接转化
            inside_code = 12288
        elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
            inside_code += 65248
        reverse_str += chr(inside_code)
    return reverse_str


def split_zh_en(ustring):
    """分离中英文"""
    zh_str = ""
    en_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code <= 256:
            en_str += uchar
        else:
            zh_str += uchar
    if not zh_str:
        zh_str = en_str
    return zh_str.strip(), en_str.strip()


def split_number_en(ustring):
    return [''.join(list(g)) for k, g in groupby(ustring, key=lambda x: x.isdigit())]