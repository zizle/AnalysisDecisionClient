# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-17
# ------------------------

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


# 绘制图形UI与显示图形的页面通讯媒介
class ReviewChartChannel(QObject):
    reset_options = pyqtSignal(str)
    resize_chart = pyqtSignal(int, int)
    show_watermark = pyqtSignal(bool, str)

    # @pyqtSlot(str)
    # def get_province_warehouses(self, province):
    #     self.request_province_warehouses.emit(province)
