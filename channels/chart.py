# _*_ coding:utf-8 _*_
# @File  : chart.py
# @Time  : 2020-09-06 19:23
# @Author: zizle
from PyQt5.QtCore import QObject, pyqtSignal


class ChartOptionChannel(QObject):
    # 参数1：图表类型(normal,season); 参数2：图表配置项; 参数3：作图的源数据
    chartSource = pyqtSignal(str, str, str)
