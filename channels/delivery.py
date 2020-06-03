# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-27
# ------------------------

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


# 交割主窗口与地图页面的交互通道
class WarehouseMapChannel(QObject):
    refresh_warehouses = pyqtSignal(list)
    resize_map = pyqtSignal(int, int)

    request_province_warehouses = pyqtSignal(str)
    request_warehouse_detail = pyqtSignal(int)

    @pyqtSlot(str)
    def get_province_warehouses(self, province):
        self.request_province_warehouses.emit(province)  # 获取省份的全部仓库

    @pyqtSlot(int)
    def get_warehouse_detail(self, wh_id):
        self.request_warehouse_detail.emit(wh_id)


