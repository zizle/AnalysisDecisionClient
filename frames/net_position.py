# _*_ coding:utf-8 _*_
# @File  : net_position.py
# @Time  : 2020-08-21 11:12
# @Author: zizle

import json
from PyQt5.QtWidgets import qApp, QTableWidgetItem
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor
from configs import SERVER
from utils.constant import VARIETY_ZH
from .net_position_ui import NetPositionUI


class NetPosition(NetPositionUI):
    def __init__(self, *args, **kwargs):
        super(NetPosition, self).__init__(*args, **kwargs)
        self.timeout_count = 0                    # 计算显示的次数,虚假显示‘正在计算’字样
        self.tips_animation_timer = QTimer(self)  # 显示文字提示的timer
        self.tips_animation_timer.timeout.connect(self.animation_tip_text)

        self.query_button.clicked.connect(self.get_net_position)

    def keyPressEvent(self, event):
        """ Ctrl + C复制表格内容 """
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            # 获取表格的选中行
            selected_ranges = self.data_table.selectedRanges()[0]
            text_str = ""
            # 行
            for row in range(selected_ranges.topRow(), selected_ranges.bottomRow() + 1):
                row_str = ""
                # 列
                for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn() + 1):
                    item = self.data_table.item(row, col)
                    row_str += item.text() + '\t'
                text_str += row_str + '\n'
            clipboard = qApp.clipboard()
            clipboard.setText(text_str)

    def animation_tip_text(self):
        """ 动态展示查询文字提示 """
        tips = self.tip_label.text()
        tip_points = tips.split(' ')[1]
        if self.timeout_count >= 10:
            text = "正在计算结果 "
        else:
            text = "正在查询数据 "
        if len(tip_points) > 2:
            self.tip_label.setText(text)
        else:
            self.tip_label.setText(text + "·" * (len(tip_points) + 1))
        self.timeout_count += 1   # 计数

    def get_net_position(self):
        """ 获取净持仓数据 """
        self.tips_animation_timer.start(400)
        net_work = getattr(qApp, '_network')
        url = SERVER + "position/all-variety/?interval_days=" + str(self.interval_days.value())
        reply = net_work.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.all_variety_position_reply)

    def all_variety_position_reply(self):
        """ 全品种净持仓数据返回 """
        reply = self.sender()
        if reply.error():
            self.tip_label.setText("获取数据失败:{} ".format(reply.error()))
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode('utf-8'))
        reply.deleteLater()
        self.show_data_in_table(data['data'], data['header_keys'])

    def show_data_in_table(self, show_data, header_keys):
        """ 将数据在表格中展示出来 """
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)
        self.tips_animation_timer.stop()  # 停止计时
        self.timeout_count = 0            # 计数归0
        self.tip_label.setText("获取结果成功! ")
        # 生成表格的列头
        self.data_table.setColumnCount(len(header_keys) * 2)
        interval_day = self.interval_days.value()
        for count in range(2):
            for index, h_key in enumerate(header_keys):
                if index == 0:
                    item = QTableWidgetItem('品种')
                elif index == 1:
                    item = QTableWidgetItem(h_key)
                else:
                    item = QTableWidgetItem(str((index - 1) * interval_day) + "天前")
                setattr(item, 'key', h_key)
                self.data_table.setHorizontalHeaderItem(index + count * len(header_keys), item)

        is_pre_half = True
        for variety, variety_values in show_data.items():
            row = self.data_table.rowCount()
            if is_pre_half:
                col_start = 0
                col_end = len(header_keys)
                self.data_table.insertRow(row)
            else:
                row -= 1
                col_start = len(header_keys)
                col_end = self.data_table.columnCount()
            for col in range(col_start, col_end):
                data_key = getattr(self.data_table.horizontalHeaderItem(col), 'key')
                if col == col_start:
                    v_zh = VARIETY_ZH.get(variety_values['variety_en'], variety_values['variety_en'])
                    item = QTableWidgetItem(v_zh)
                    item.setForeground(QBrush(QColor(180, 60, 60)))
                else:
                    item = QTableWidgetItem(str(int(variety_values.get(data_key, 0))))
                item.setTextAlignment(Qt.AlignCenter)

                self.data_table.setItem(row, col, item)
            is_pre_half = not is_pre_half








