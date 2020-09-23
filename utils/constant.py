# _*_ coding:utf-8 _*_
# @File  : constant.py
# @Time  : 2020-08-21 12:50
# @Author: zizle


# 所有品种对应的中文名
VARIETY_ZH = {
    'A': '黄大豆1号',
    'B': '黄大豆2号',
    'C': '玉米',
    'CS': '玉米淀粉',
    'EB': '苯乙烯',
    'EG': '乙二醇',
    'I': '铁矿石',
    'J': '焦炭',
    'JD': '鸡蛋',
    'JM': '焦煤',
    'L': '聚乙烯',
    'M': '豆粕',
    'P': '棕榈油',
    'PG': '液化石油气',
    'PP': '聚丙烯',
    'RR': '粳米',
    'V': '聚氯乙烯',
    'Y': '豆油',
    'IC': '中证500股指',
    'IF': '沪深300股指',
    'IH': '上证50股指',
    'T': '10年期国债',
    'TF': '5年期国债',
    'TS': '2年期国债期',
    'AP': '苹果',
    'CF': '棉花',
    'CJ': '红枣',
    'CY': '棉纱',
    'FG': '玻璃',
    'JR': '粳稻',
    'LR': '晚籼',
    'MA': '甲醇',
    'OI': '菜油',
    'PM': '普麦',
    'RI': '早籼',
    'RM': '菜粕',
    'RS': '菜籽',
    'SA': '纯碱',
    'SF': '硅铁',
    'SM': '锰硅',
    'SR': '白糖',
    'TA': '精对苯二甲酸',
    'UR': '尿素',
    'WH': '强麦',
    'ZC': '动力煤',
    'AG': '白银',
    'AL': '铝',
    'AU': '黄金',
    'BU': '沥青',
    'CU': '铜',
    'FU': '燃料油',
    'HC': '热轧卷板',
    'LU': '低硫燃料油',
    'NI': '镍',
    'NR': '20号胶',
    'PB': '铅',
    'RB': '螺纹钢',
    'RU': '天然橡胶',
    'SC': '原油',
    'SN': '锡',
    'SP': '纸浆',
    'SS': '不锈钢',
    'WR': '线材',
    'ZN': '锌',
}

# 中文对应品种交易代码(使用场景:提取现货数据;提取每日仓单)
VARIETY_EN = {
    '铜': 'CU',
    '铝': 'AL',
    '铅': 'PB',
    '锌': 'ZN',
    '锡': 'SN',
    '镍': 'NI',
    '铁矿石': 'I',
    '热轧卷板': 'HC',
    '螺纹钢': 'RB',
    '螺纹钢仓库': 'RB',
    '螺纹钢厂库': 'RB',
    '线材': 'WR',
    '不锈钢': 'SS',
    '不锈钢仓库': 'SS',
    '硅铁': 'SF',
    '硅锰': 'SM',
    '焦煤': 'JM',
    '焦炭': 'J',
    '动力煤': 'ZC',
    '黄金': 'AU',
    '白银': 'AG',
    '大豆': 'A',
    '豆粕': 'M',
    '豆油': 'Y',
    '棕榈油': 'P',
    '粳米': 'RR',
    '白糖': 'SR',
    '棉花': 'CF',
    '棉纱': 'CY',
    '苹果': 'AP',
    '红枣': 'CJ',
    '鸡蛋': 'JD',
    '菜粕': 'RM',
    '菜油': 'OI',
    '玉米': 'C',
    '淀粉': 'CS',
    'LLDPE': 'L',
    'PP': 'PP',
    'PVC': 'V',
    '苯乙烯': 'EB',
    '全乳胶': 'RU',
    '天然橡胶': 'RU',
    '20号胶': 'NR',
    'STR20': 'NR',
    '甲醇': 'MA',
    '尿素': 'UR',
    '玻璃': 'FG',
    '纯碱': 'SA',
    '乙二醇': 'EG',
    'PTA': 'TA',
    '纸浆': 'SP',
    '纸浆仓库': 'SP',
    '纸浆厂库': 'SP',
    '沥青': 'BU',
    '石油沥青仓库': 'BU',
    '石油沥青厂库': 'BU',
    '液化气': 'PG',
    '燃料油': 'FU',
    '原油': 'SC',
    '中质含硫原油': 'SC',
}