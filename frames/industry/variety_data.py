# _*_ coding:utf-8 _*_
# @File  : variety_data.py
# @Time  : 2020-09-03 8:29
# @Author: zizle
from .variety_data_ui import VarietyDataUI


class VarietyData(VarietyDataUI):
    def __init__(self, *args, **kwargs):
        super(VarietyData, self).__init__(*args, **kwargs)
        self.variety_tree.left_mouse_clicked.connect(self.selected_variety_event)

    def selected_variety_event(self, variety_id, group_text, variety_en):
        """ 选择了某个品种事件 """
        print(group_text, variety_id, variety_en)