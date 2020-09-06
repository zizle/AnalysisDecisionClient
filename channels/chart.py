# _*_ coding:utf-8 _*_
# @File  : chart.py
# @Time  : 2020-09-06 19:23
# @Author: zizle
from PyQt5.QtCore import QObject, pyqtSignal


class ChartOptionChannel(QObject):
    chart_data = pyqtSignal(str, str)
