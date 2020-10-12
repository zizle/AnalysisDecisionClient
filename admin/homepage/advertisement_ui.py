# _*_ coding:utf-8 _*_
# @File  : advertisement_ui.py
# @Time  : 2020-10-12 15:50
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QPushButton, QFrame


class HomepageAdAdminUI(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(HomepageAdAdminUI, self).__init__(*args, **kwargs)
        self.ad_table = QTableWidget(self)
        self.ad_table.setFrameShape(QFrame.NoFrame)

        self.addTab(self.ad_table, "当前广告")

        new_ad_widget = QWidget(self)
        create_layout = QVBoxLayout()

        new_ad_widget.setLayout(create_layout)
        self.addTab(new_ad_widget, "新建广告")


    def get_current_advertisement(self):
        """ 获取当前所有广告 """


