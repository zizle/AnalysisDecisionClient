# _*_ coding:utf-8 _*_
# @File  : delivery.py
# @Time  : 2020-09-22 14:21
# @Author: zizle
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import Qt
from .delivery_ui import DeliveryAdminUI, WarehouseNumber, WarehouseManagerUI


class DeliveryAdmin(DeliveryAdminUI):
    def __init__(self, *args, **kwargs):
        super(DeliveryAdmin, self).__init__(*args, **kwargs)
        # 添加菜单(menu_id为stacked_widget的索引)
        for menu_item in [
            {"menu_id": "0", "menu_name": "仓库编号"},
            {"menu_id": "1", "menu_name": "仓库管理"},
            {"menu_id": "2", "menu_name": "品种交割信息"},
        ]:
            item = QListWidgetItem(menu_item["menu_name"])
            item.setData(Qt.UserRole, menu_item["menu_id"])
            self.menu_list.addItem(item)

        # 创建stacked_widget加入
        self.warehouse_number_widget = WarehouseNumber(self)
        self.stacked_frame.addWidget(self.warehouse_number_widget)

        self.warehouse_manger_widget = WarehouseManagerUI(self)
        self.stacked_frame.addWidget(self.warehouse_manger_widget)

        self.menu_list.itemClicked.connect(self.select_manager_menu)

    def select_manager_menu(self, item):
        """ 选择了菜单 """
        menu_id = item.data(Qt.UserRole)
        self.stacked_frame.setCurrentIndex(int(menu_id))
