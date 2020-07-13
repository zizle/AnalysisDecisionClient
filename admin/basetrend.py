# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-19
# ------------------------
import os
import re
import xlrd
import json
import time
import datetime
import requests
import pickle
import pandas as pd
import math
from PyQt5.QtWidgets import QApplication,QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QComboBox, QTableWidget, \
    QPushButton, QAbstractItemView, QHeaderView, QTableWidgetItem, QDialog, QMessageBox, QLineEdit, QFileDialog,QMenu,QFrame, \
    QGroupBox, QCheckBox, QTextEdit, QGridLayout, QSpinBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QUrl, QThread, QTimer, QMargins, QRegExp
from PyQt5.QtGui import QCursor, QIcon, QDoubleValidator
import settings
from widgets import LoadedPage
from channels.trend import ReviewChartChannel
from utils.charts import chart_options_handler


# 数据图列配置的按钮
class ChartAxisOptionButton(QPushButton):
    add_axis_target = pyqtSignal(str, str)

    def __init__(self, axis_name, axis_type, *args, **kwargs):
        super(ChartAxisOptionButton, self).__init__(*args, **kwargs)
        self.axis_name = axis_name
        self.axis_type = axis_type
        self.clicked.connect(self.emit_info)

    def emit_info(self):
        self.add_axis_target.emit(self.axis_name, self.axis_type)


# 重写事件，防止鼠标滚轮键影响页面整个页面滚动
class WebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super(WebEngineView, self).__init__(*args, **kwargs)
        self.load(QUrl("file:///pages/trend/review_chart.html"))  # 加载页面
        # 设置与页面通讯的通道
        channel_qt_obj = QWebChannel(self.page())  # 实例化qt信道对象,必须传入页面参数
        self.contact_channel = ReviewChartChannel()  # 页面信息交互通道
        self.page().setWebChannel(channel_qt_obj)
        channel_qt_obj.registerObject("pageContactChannel", self.contact_channel)  # 信道对象注册信道，只能注册一个

    def wheelEvent(self, event):
        super(WebEngineView, self).wheelEvent(event)
        event.accept()

    def resizeEvent(self, event):
        self.resize_page_chart(True)

    def resize_page_chart(self, is_loaded):
        if is_loaded:
            self.contact_channel.resize_chart.emit(self.width() - 22, self.height() - 11)  # 布局默认的外边距是11px

    def reset_chart_options(self, options):
        self.resize_page_chart(True)
        self.contact_channel.reset_options.emit(json.dumps(options))


# 根据表数据画图界面
class DrawChartsDialog(QDialog):
    CHARTS = {
        'line': '线形图',
        'bar': '柱状图'
    }   # 支持的图形

    def __init__(self, table_id,variety_id, *args,**kwargs):
        super(DrawChartsDialog, self).__init__(*args, **kwargs)
        self.table_id = table_id
        self.variety_id = variety_id
        self.resize(1080, 660)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.table_headers = []
        self.headers_indexes = dict()
        # self.table_sources = None
        self.source_data_frame = None
        self.sorted_data = None
        self.has_left_axis = False

        # 轴标签
        self.axix_tags = {"left":"", "right":"", "bottom": ""}
        # 数据起终
        self.bottom_start = ""
        self.bottom_end = ""
        # 左轴数据范围
        self.left_min = ''
        self.left_max = ''
        # 右轴数据范围
        self.right_min = ''
        self.right_max = ''

        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout(self)
        right_layout = QVBoxLayout(self)

        self.target_widget = QWidget(self)
        self.target_widget.setFixedWidth(250)
        target_layout = QVBoxLayout(self)

        title_layout = QHBoxLayout(self)
        title_layout.addWidget(QLabel('标题:',self))
        self.title_edit = QLineEdit(self)
        title_layout.addWidget(self.title_edit)
        title_layout.addWidget(QLabel('大小:', self))
        self.title_size_edit = QSpinBox(self)
        self.title_size_edit.setMaximum(100)
        self.title_size_edit.setMinimum(10)
        self.title_size_edit.setValue(22)

        title_layout.addWidget(self.title_size_edit, alignment=Qt.AlignRight)

        target_layout.addLayout(title_layout)

        x_axis_layout = QHBoxLayout(self)
        x_axis_layout.addWidget(QLabel('横轴:', self))
        self.x_axis_combobox = QComboBox(self)

        x_axis_layout.addWidget(self.x_axis_combobox)
        x_axis_layout.addStretch()
        target_layout.addLayout(x_axis_layout)

        x_format_layout = QHBoxLayout(self)
        x_format_layout.addWidget(QLabel('格式:', self))
        self.date_format = QComboBox(self)
        self.date_format.addItem('年-月-日', '%Y-%m-%d')
        self.date_format.addItem('年-月', '%Y-%m')
        self.date_format.addItem('年', '%Y')
        # self.date_format.currentIndexChanged.connect(self.x_axis_changed)
        x_format_layout.addWidget(self.date_format)
        x_format_layout.addStretch()
        target_layout.addLayout(x_format_layout)

        add_target = QGroupBox("添加指标", self)
        add_target_layout = QVBoxLayout()
        self.target_list = QListWidget(self)
        add_target_layout.addWidget(self.target_list)
        options_layout = QGridLayout(self)
        self.button1 = ChartAxisOptionButton(axis_name='left',axis_type='line',text='左轴线形', parent=self)
        self.button1.add_axis_target.connect(self.add_target_index)
        self.button2 = ChartAxisOptionButton(axis_name='left',axis_type='bar',text='左轴柱状', parent=self)
        self.button2.add_axis_target.connect(self.add_target_index)
        self.button3 = ChartAxisOptionButton(axis_name='right',axis_type='line',text='右轴线形', parent=self)
        self.button3.add_axis_target.connect(self.add_target_index)
        self.button4 = ChartAxisOptionButton(axis_name='right',axis_type='bar',text='右轴柱状', parent=self)
        self.button4.add_axis_target.connect(self.add_target_index)
        options_layout.addWidget(self.button1, 0, 0)
        options_layout.addWidget(self.button2, 1, 0)
        options_layout.addWidget(self.button3, 0, 1)
        options_layout.addWidget(self.button4, 1, 1)
        add_target_layout.addLayout(options_layout)
        add_target.setLayout(add_target_layout)
        target_layout.addWidget(add_target)

        show_params_layout = QVBoxLayout()
        self.show_params = QGroupBox("已选指标", self)
        self.params_list = QListWidget(self)
        self.params_list.doubleClicked.connect(self.remove_target_index)
        show_params_layout.addWidget(self.params_list)
        self.show_params.setLayout(show_params_layout)

        target_layout.addWidget(self.show_params)

        graphic_layout = QHBoxLayout(self)
        graphic_layout.setSpacing(1)
        self.has_graphic = QCheckBox(self)
        self.has_graphic.setText("添加水印")
        self.water_graphic = QLineEdit(self)
        self.water_graphic.setText("瑞达期货研究院")
        graphic_layout.addWidget(self.has_graphic)
        graphic_layout.addWidget(self.water_graphic)
        graphic_layout.addStretch()
        target_layout.addLayout(graphic_layout)

        range_layout = QHBoxLayout(self)
        self.start_year = QSpinBox(self)
        self.end_year = QSpinBox(self)
        range_layout.addWidget(QLabel('取数范围:'))
        range_layout.addWidget(self.start_year)
        range_layout.addWidget(QLabel('到', self))
        range_layout.addWidget(self.end_year)

        # more chart configs
        self.more_configs_btn = QPushButton("更多配置",self, styleSheet="font-size:11px")
        self.more_configs_btn.clicked.connect(self.chart_more_config)
        range_layout.addWidget(self.more_configs_btn)
        range_layout.addStretch()
        target_layout.addLayout(range_layout)

        self.target_widget.setLayout(target_layout)
        target_layout.addStretch()
        left_layout.addWidget(self.target_widget)

        draw_layout = QHBoxLayout(self)
        self.confirm_to_draw = QPushButton('确认绘制', self)
        self.confirm_to_draw.clicked.connect(self.draw_chart)
        draw_layout.addWidget(self.confirm_to_draw)
        self.season_draw = QPushButton('季节图表', self)
        self.season_draw.clicked.connect(self.draw_season_chart)
        draw_layout.addWidget(self.season_draw)

        left_layout.addLayout(draw_layout)
        # 右侧显示图形和数据表格
        self.chart_widget = WebEngineView(self)

        self.table_widget = QTableWidget(self)
        self.table_widget.setFixedHeight(220)
        self.table_widget.setEditTriggers(QHeaderView.NoEditTriggers)
        right_layout.addWidget(self.chart_widget)

        config_layout = QHBoxLayout(self)
        config_layout.addWidget(QLabel("解读:", self))
        self.decipherment_edit = QLineEdit(self)
        self.decipherment_edit.setPlaceholderText("在此输入对此图形的解读,文字将展示在图形下方.(非必填)...")
        config_layout.addWidget(self.decipherment_edit)

        self.save_config = QPushButton('保存配置',self)
        menu = QMenu(self)
        normal_action = menu.addAction("普通图形")
        normal_action.setIcon(QIcon("media/nor_chart.png"))
        normal_action.triggered.connect(self.save_chart_options_to_server)
        season_action = menu.addAction("季节图形")
        season_action.setIcon(QIcon("media/multi_chart.png"))
        season_action.triggered.connect(self.season_chart_options_to_server)
        self.save_config.setMenu(menu)

        # self.save_config.clicked.connect(self.save_chart_options_to_server)
        config_layout.addWidget(self.save_config)

        right_layout.addLayout(config_layout)
        # right_layout.addWidget(self.save_config, alignment=Qt.AlignRight)
        right_layout.addWidget(self.table_widget)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setLayout(layout)
        self._get_detail_table_data()

    # 获取表格源数据
    def _get_detail_table_data(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/'
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            settings.logger.error("用户进入绘图获取表格源数据失败:{}".format(e))
        else:
            table_records = response['records']
            table_headers = table_records.pop(0)  # 表头行
            free_row = table_records.pop(0)  # 第三行自由行
            # 将数据进行日期行排序
            self.sorted_source_table_records(table_records, 'column_0')
            # 排序后加入自由行
            if self.sorted_data is None:
                return
            table_records = self.sorted_data.to_dict(orient="records")
            table_records.insert(0, free_row)  # 加入第三 行
            # 删除表头多余的项，并列表化
            del table_headers['id']
            del table_headers['create_time']
            del table_headers['update_time']
            self.table_headers = table_headers
            # 设置表头的选项
            for header_index, header_text in self.table_headers.items():
                self.x_axis_combobox.addItem(header_text, header_index)
                item = QListWidgetItem(header_text)
                item.index = header_index
                self.target_list.addItem(item)

            # 横轴选项改变重新排序DF的信号连接
            self.x_axis_combobox.currentIndexChanged.connect(self.x_axis_changed)
            # 表格展示数据
            self.table_show_data(self.table_headers, table_records)

    # 对源数据进行排序
    def sorted_source_table_records(self, source_data, sort_column):
        source_df = pd.DataFrame(source_data) if source_data else self.sorted_data
        if sort_column == 'column_0':
            source_df['column_0'] = pd.to_datetime(source_df['column_0'], format='%Y-%m-%d')
            source_df = source_df.sort_values(by="column_0")  # 排序
            source_df['column_0'] = source_df['column_0'].apply(lambda x: x.strftime('%Y-%m-%d'))  # 转为原格式
        else:
            source_df = source_df.sort_values(by=sort_column)
        source_df.reset_index(drop=True, inplace=True)  # 重置数据索引
        self.sorted_data = source_df.copy()
        del source_df  # 释放内存(在函数内创建或许无需释放，但不知道.copy()会不会影响，还是放一下吧)
        self.set_source_start_and_end(sort_column)  # 根据排序的索引进行数据起始值和终止值的设置

    # 设置起始和终止值的设置
    def set_source_start_and_end(self, column):
        if column == "column_0":
            # 读取数据的第一个和最后一个进行格式化后设置
            start_date = self.sorted_data.loc[0]['column_0']
            end_date = self.sorted_data.loc[self.sorted_data.shape[0] - 1]['column_0']
            self.start_year.setMinimum(int(start_date[:4]))
            self.start_year.setMaximum(int(end_date[:4]))
            self.end_year.setMinimum(int(start_date[:4]))
            self.end_year.setMaximum(int(end_date[:4]))
            self.end_year.setValue(int(end_date[:4]))
        else:
            # 设置数据的个数值
            self.start_year.setMinimum(0)
            self.start_year.setMaximum(self.sorted_data.shape[0])
            self.start_year.setValue(0)
            self.end_year.setMinimum(0)
            self.end_year.setMaximum(self.sorted_data.shape[0])
            self.end_year.setValue(self.sorted_data.shape[0])

    # 排序完的数据（加入自由行）数据进行显示
    def table_show_data(self, headers_dict, records):
        headers = [header for header in headers_dict.values()]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setRowCount(len(records))
        self.table_widget.setHorizontalHeaderLabels(headers)
        # self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for row, row_item in enumerate(records):
            for col in range(self.table_widget.columnCount()):
                key = "column_{}".format(col)
                item = QTableWidgetItem(row_item[key])
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, col, item)

    # 添加作图的指标
    def add_target_index(self, axis_name, axis_type):
        current_index_item = self.target_list.currentItem()
        if not current_index_item:
            QMessageBox.information(self, '错误', '先选择一个数据指标')
            return
        col_index = current_index_item.index
        text = current_index_item.text()
        if axis_name == 'left':
            item = QListWidgetItem("左轴" + self.CHARTS[axis_type] + " = " + text)
            item.axis_pos = 'left'
            item.column_index = col_index
            item.chart_type = axis_type
            item.no_zero = Qt.Unchecked
            self.has_left_axis = True
        elif axis_name == 'right':
            if not self.has_left_axis:
                QMessageBox.information(self, '错误', '请先添加一个左轴数据列')
                return
            item = QListWidgetItem("右轴" + self.CHARTS[axis_type] + " = " + text)
            item.axis_pos = 'right'
            item.column_index = col_index
            item.chart_type = axis_type
            item.no_zero = Qt.Unchecked
        else:
            QMessageBox.information(self, '错误', '内部发生一个未知错误')
            return
        self.params_list.addItem(item)

    # 移除作图的指标
    def remove_target_index(self, index):
        self.params_list.takeItem(self.params_list.currentRow())

    # 横轴绘图指标发生改变时执行的槽函数
    def x_axis_changed(self):
        sort_column = self.sender().currentData()
        self.sorted_source_table_records(None, sort_column)

    # 更多的配置信息(轴的信息,固定起始终止，去0等)
    def chart_more_config(self):
        def set_bottom_start(checked):
            if checked == 2:
                self.bottom_start = str(self.start_year.value())
            else:
                self.bottom_start = ""

        def set_bottom_end(checked):
            if checked == 2:
                self.bottom_end = str(self.end_year.value())
            else:
                self.bottom_end = ""

        def change_left_tag(text):
            self.axix_tags["left"] = text

        def change_right_tag(text):
            self.axix_tags['right'] = text

        def change_bottom_tag(text):
            self.axix_tags["bottom"] = text

        def float_validator(vaule):
            try:
                float(vaule)
            except ValueError:
                return ''
            else:
                return vaule

        def change_left_min_value(value):
            self.left_min = float_validator(value)

        def change_left_max_value(value):
            self.left_max = float_validator(value)

        def change_right_min_value(value):
            self.right_min = float_validator(value)

        def change_right_max_value(value):
            self.right_max = float_validator(value)

        popup = QDialog(self)
        popup.setWindowTitle("更多配置")
        layout = QVBoxLayout(popup)

        ######### 左轴参数 ##########

        layout.addWidget(QLabel('左轴调整:', popup, objectName='optsLabel'))
        left_unit_layout = QHBoxLayout(popup)
        left_unit_layout.setContentsMargins(7, 0, 0, 0)
        l = QLabel("名称:", popup)
        left_tag = QLineEdit(popup)
        left_tag.setText(self.axix_tags["left"])
        left_tag.textChanged.connect(change_left_tag)
        left_unit_layout.addWidget(l)
        left_unit_layout.addWidget(left_tag)

        lable_ = QLabel("最小值:", popup)
        left_min = QLineEdit(popup)
        left_min.setText(self.left_min)
        left_min.textChanged.connect(change_left_min_value)
        left_unit_layout.addWidget(lable_)
        left_unit_layout.addWidget(left_min)

        lable_ = QLabel("最大值:", popup)
        left_max = QLineEdit(popup)
        left_max.setText(self.left_max)
        left_max.textChanged.connect(change_left_max_value)
        left_unit_layout.addWidget(lable_)
        left_unit_layout.addWidget(left_max)

        left_unit_layout.addStretch()
        layout.addLayout(left_unit_layout)

        ######## 右轴参数 ##########
        layout.addWidget(QLabel('右轴调整:', popup, objectName='optsLabel'))
        l = QLabel("名称:", popup)
        right_tag = QLineEdit(popup)
        right_tag.setText(self.axix_tags["right"])
        right_tag.textChanged.connect(change_right_tag)
        right_unit_layout = QHBoxLayout(popup)
        right_unit_layout.setContentsMargins(7, 0, 0, 0)
        right_unit_layout.addWidget(l)
        right_unit_layout.addWidget(right_tag)

        lable_ = QLabel("最小值:", popup)
        right_min = QLineEdit(popup)
        right_min.setText(self.right_min)
        right_min.textChanged.connect(change_right_min_value)
        right_unit_layout.addWidget(lable_)
        right_unit_layout.addWidget(right_min)

        lable_ = QLabel("最大值:", popup)
        right_max = QLineEdit(popup)
        right_max.setText(self.right_max)
        right_max.textChanged.connect(change_right_max_value)
        right_unit_layout.addWidget(lable_)
        right_unit_layout.addWidget(right_max)

        right_unit_layout.addStretch()
        layout.addLayout(right_unit_layout)

        ########### 横轴设置 ##########

        layout.addWidget(QLabel('横轴调整:', objectName='optsLabel'))
        l = QLabel("名称:", popup)
        bottom_tag = QLineEdit(popup)
        bottom_tag.setText(self.axix_tags["bottom"])
        bottom_tag.textChanged.connect(change_bottom_tag)
        bottom_unit_layout = QHBoxLayout(popup)
        bottom_unit_layout.setContentsMargins(7, 0, 0, 0)
        bottom_unit_layout.addWidget(l)
        bottom_unit_layout.addWidget(bottom_tag)

        limit_start = QCheckBox(popup)
        limit_start.setText("固定起始")
        if self.bottom_start:
            limit_start.setCheckState(Qt.Checked)
        limit_start.stateChanged.connect(set_bottom_start)
        bottom_unit_layout.addWidget(limit_start)
        limit_end = QCheckBox(popup)
        limit_end.setText("固定结束")
        limit_end.stateChanged.connect(set_bottom_end)
        if self.bottom_end:
            limit_end.setCheckState(Qt.Checked)
        bottom_unit_layout.addWidget(limit_end)
        bottom_unit_layout.addStretch()
        layout.addLayout(bottom_unit_layout)

        layout.addWidget(QLabel("数据是否去 0:",popup, objectName='optsLabel'))
        for index in range(self.params_list.count()):
            item = self.params_list.item(index)
            no_zero_checked = QCheckBox(popup)
            no_zero_checked.stateChanged.connect(self.axis_no_zero_changed)
            no_zero_checked.setText(item.text())
            no_zero_checked.setCheckState(item.no_zero)  # Qt.Checked,
            layout.addWidget(no_zero_checked)

        close_btn = QPushButton("确定", popup)
        close_btn.clicked.connect(popup.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        popup.setLayout(layout)
        popup.setMaximumWidth(420)
        popup.setStyleSheet("""
        #optsLabel{padding: 3px; font-size:14px;background:rgb(200,220,230);border-radius: 3px}
        """)
        popup.exec_()

    # 数据去0设置
    def axis_no_zero_changed(self, state):
        checked = self.sender()
        # print(checked.checkState(), checked.text())
        for index in range(self.params_list.count()):
            item = self.params_list.item(index)
            if item.text() == checked.text():
                item.no_zero = checked.checkState()
                break

    # 预处理图表的当前配置项(即保存到server的json配置信息)
    def get_pretreatment_options(self):  # 单表绘制
        # 标题
        title = self.title_edit.text()
        # 获取x轴，左轴和右轴的数据索引轴
        x_axis = self.x_axis_combobox.currentData()
        left_axis = list()  # 左轴
        right_axis = list()  # 右轴
        for index in range(self.params_list.count()):
            item = self.params_list.item(index)
            if item.axis_pos == 'left':
                left_axis.append({"col_index": item.column_index, "chart_type": item.chart_type, "no_zero": item.no_zero})
            else:
                right_axis.append({"col_index": item.column_index, "chart_type": item.chart_type, "no_zero": item.no_zero})

        # 返回预处理的配置项
        # typec表示图形的类型，single单表绘制,compose组合表,calculate计算绘制
        return {
            'typec': 'single',
            'table_id': self.table_id,
            'title': {'text': title, 'left': 'center', 'textStyle': {'fontSize': self.title_size_edit.value()}},
            'x_axis': [{"col_index": x_axis, "start": self.bottom_start, "end": self.bottom_end, 'date_format': self.date_format.currentData()}],
            'y_left': left_axis,
            'y_left_min': self.left_min,
            'y_left_max': self.left_max,
            'y_right': right_axis,
            'y_right_min': self.right_min,
            'y_right_max': self.right_max,
            'watermark': self.has_graphic.checkState(),
            'watermark_text': self.water_graphic.text(),
            'axis_tags': self.axix_tags
        }

    # 保存当前数据表的设置到服务端存为我的数据表(普通作图的配置)
    def save_chart_options_to_server(self):
        options_json = self.get_pretreatment_options()
        y_num = len(options_json['y_left'])
        if y_num <= 0:
            y_num = len(options_json['y_right'])
        if not options_json['title'] or y_num <= 0:
            QMessageBox.information(self, '错误', '请设置标题并至少添加一个左轴或右轴指标...')
            return
        # 向后台发起保存json配置数据
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'trend/table-chart/',
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "utoken": settings.app_dawn.value("AUTHORIZATION"),
                    "chart_options": options_json,
                    "title": options_json['title']['text'],
                    "variety_id": self.variety_id,
                    "table_id": self.table_id,
                    "decipherment": self.decipherment_edit.text().strip()
                })
            )
            response = json.loads(r.content.decode("utf-8"))
            if r.status_code != 201:
                raise ValueError(response["message"])
        except Exception as e:
            QMessageBox.information(self, "出错了", str(e))
        else:
            QMessageBox.information(self, "成功", response['message'])

    # 保存季节图表的设置到服务端为我的数据表
    def season_chart_options_to_server(self):
        QMessageBox.information(self, '提示', '暂不支持保存季节图表的配置...')

    # 切片数据范围返回新DataFrame
    def get_splice_df(self, x_column):
        if x_column == 'column_0':
            start_year = datetime.datetime.strptime(str(self.start_year.value()), '%Y').strftime('%Y-%m-%d')
            end_year = datetime.datetime.strptime(str(self.end_year.value() + 1), '%Y').strftime("%Y-%m-%d")
            # print(start_year, end_year)
            # 取数
            sourcedf = self.sorted_data[(start_year <= self.sorted_data['column_0']) & (self.sorted_data['column_0'] < end_year)].copy()
        else:
            start_row = self.start_year.value()
            end_row = self.end_year.value()
            # print(start_row, end_row)
            sourcedf = self.sorted_data[start_row:end_row].copy()
        return sourcedf

    # 获取预处理后的配置项生成图形配置并传入绘图
    def draw_chart(self):
        pretreatment_options = self.get_pretreatment_options()
        # 根据当前的预处理后的配置选项和已排序后的数据表进行图形配置options的生成
        # print(pretreatment_options)
        x_axis = pretreatment_options['x_axis'][0]
        # 根据x轴转数据格式
        chart_src_data = self.get_splice_df(x_axis['col_index'])
        options = chart_options_handler(chart_src_data, self.table_headers, pretreatment_options)
        self.reset_chart_options(options)

    # 根据预处理后的配置项生成季节图形配置并传入绘图
    def draw_season_chart(self):
        print('绘制季节图表')
        # 1 判断横轴是日期行
        x_bottom = self.x_axis_combobox.currentData()
        if x_bottom != "column_0":
            QMessageBox.information(self, '错误', '横轴指标类型错误..')
            return
        # 2 判断只能有一个左轴或右轴数据
        left_axis = {}
        right_axis = {}
        for index in range(self.params_list.count()):
            item = self.params_list.item(index)
            if item.axis_pos == 'left':
                left_axis[item.column_index] = item.chart_type
            else:
                right_axis[item.column_index] = item.chart_type
        if all([left_axis, right_axis]):
            QMessageBox.information(self, '错误', '只允许一个轴指标..')
            return
        if left_axis and len(left_axis) > 1:
            QMessageBox.information(self, '错误', '左轴仅允许选中一个指标..')
            return
        if right_axis and len(right_axis) > 1:
            QMessageBox.information(self, '错误', '右轴仅允许选中一个指标..')
            return
        # 3 进行数据处理
        start_date = str(self.start_year.value())
        end_date = str(self.end_year.value())
        # 3-1 生成起始日期的年份列表
        date_list = [datetime.datetime.strptime(str(date), "%Y").strftime('%Y-%m-%d') for date in range(int(start_date[:4]), int(end_date[:4]) + 1)]
        # 弹窗设置年份参数
        # print(date_list)
        # 3-2 取min_index,当min_index+1<=max_index切割数据
        if len(date_list) <= 0:
            QMessageBox.information(self, '错误', '作图源数据有误..')
            return
        min_index, max_index = 0, len(date_list) - 1
        split_data_dict = dict()
        # if len(date_list) > 1:
        while min_index < max_index:
            year_data_frame = self.sorted_data[(date_list[min_index] <= self.sorted_data['column_0']) & (self.sorted_data['column_0'] < date_list[min_index + 1])].copy()
            year_data_frame['column_0'] = year_data_frame['column_0'].apply(lambda x: x[5:])
            split_data_dict[date_list[min_index]] = year_data_frame
            min_index += 1
        year_data_frame = self.sorted_data[date_list[max_index] <= self.sorted_data['column_0']].copy()
        year_data_frame['column_0'] = year_data_frame['column_0'].apply(lambda x: x[5:])
        split_data_dict[date_list[max_index]] = year_data_frame
        # else:
        #     year_data_frame = self.sorted_data.copy()
        #     year_data_frame['column_0'] = year_data_frame['column_0'].apply(lambda x: x[5:])
        #     split_data_dict[date_list[0]] = year_data_frame
        # 4 生成x横轴信息,获取y轴数据进行绘图
        x_start, x_end = datetime.datetime.strptime('20200101','%Y%m%d'), datetime.datetime.strptime('20201231','%Y%m%d')
        x_axis = list()
        while x_start <= x_end:
            x_axis.append(x_start.strftime('%m-%d'))
            x_start += datetime.timedelta(days=1)
        # print(x_axis)
        # 4-1 生成y轴的配置
        # print(split_data_dict)
        y_axis = [{'type': 'value'}, {'type': 'value'}]
        series = list()
        legend_data = list()
        for col_key, chart_type in left_axis.items():
            for date_key in date_list:
                source_df = split_data_dict[date_key]
                left_series = dict()
                left_series['type'] = chart_type
                left_series['name'] = date_key[:4]
                left_series['yAxisIndex'] = 0
                a = source_df['column_0'].values.tolist()  # 时间
                b = source_df[col_key].values.tolist()  # 数值
                left_series['data'] = [*zip(a, b)]
                series.append(left_series)
                legend_data.append(date_key[:4])

        for col_key, chart_type in right_axis.items():
            for date_key in date_list:
                source_df = split_data_dict[date_key]
                right_series = dict()
                right_series['type'] = chart_type
                right_series['name'] = date_key[:4]
                right_series['yAxisIndex'] = 1
                a = source_df['column_0'].values.tolist()  # 时间
                b = source_df[col_key].values.tolist()  # 数值
                right_series['data'] = [*zip(a, b)]
                series.append(right_series)
                legend_data.append(date_key[:4])

        # 5 生成配置项进行绘图
        title = self.title_edit.text()
        graphic = {
            'type': 'group',
            'rotation': math.pi / 4,
            'bounding': 'raw',
            'right': 110,
            'bottom': 110,
            'z': 100,
            'children': [
                {
                    'type': 'rect',
                    'left': 'center',
                    'top': 'center',
                    'z': 100,
                    'shape': {
                        'width': 400,
                        'height': 50
                    },
                    'style': {
                        'fill': 'rgba(0,0,0,0.3)'
                    }
                },
                {
                    'type': 'text',
                    'left': 'center',
                    'top': 'center',
                    'z': 100,
                    'style': {
                        'fill': '#fff',
                        'text': self.water_graphic.text(),
                        'font': 'bold 26px Microsoft YaHei'
                    }
                }
            ]
        }
        option = {
            'title': {'text': title, 'left': 'center', 'textStyle': {'fontSize': self.title_size_edit.value()}},
            'legend': {'data': legend_data, 'bottom': 13},
            'tooltip': {'axisPointer': {'type': 'cross'}},
            'grid': {
                'top': self.title_size_edit.value() + 15,
                'left': 5,
                'right': 5,
                'bottom': 20 * (len(legend_data) / 10 + 1) + 13,
                'show': False,
                'containLabel': True,
            },
            'xAxis': {
                'type': 'category',
                'data': x_axis
            },
            'yAxis': y_axis,
            'series': series,
            'dataZoom': [{
                'type': 'slider',
                'start': 0,
                'end': 100,
                'bottom': 0,
                'height': 15,
                'handleIcon': 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                'handleSize': '80%',
                'handleStyle': {
                    'color': '#fff',
                    'shadowBlur': 3,
                    'shadowColor': 'rgba(0, 0, 0, 0.6)',
                    'shadowOffsetX': 2,
                    'shadowOffsetY': 2
                }
            }],
        }
        if self.has_graphic.isChecked():
            option['graphic'] = graphic
        self.reset_chart_options(option)

    # 图表配置传入界面显示
    def reset_chart_options(self, option):
        self.chart_widget.reset_chart_options(option)


# 数据表的详情信息
class TableDetailRecordOpts(QDialog):
    def __init__(self, table_id, option, *args, **kwargs):
        super(TableDetailRecordOpts, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(1000, 630)
        self.table_id = table_id
        self.option = option
        layout = QVBoxLayout(self)
        opts_layout = QHBoxLayout(self)
        self.tips_label = QLabel("双击单元格修改数据后,点击对应行【修改】按钮进行修改.", self)
        opts_layout.addWidget(self.tips_label)
        self.paste_button = QPushButton("批量粘贴", self)
        self.paste_button.clicked.connect(self.paste_new_data)
        opts_layout.addWidget(self.paste_button, alignment=Qt.AlignLeft)
        self.add_new_row = QPushButton("增加一行", self)
        self.add_new_row.clicked.connect(self.add_new_row_record)
        opts_layout.addWidget(self.add_new_row)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)
        self.table = QTableWidget(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.table.cellClicked.connect(self.table_cell_clicked)
        layout.addWidget(self.table)
        self.commit_button = QPushButton("确定增加", self)
        self.commit_button.clicked.connect(self.commit_new_contents)
        layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        self.setLayout(layout)
        if option == 'modify':
            self.tips_label.show()
            self.paste_button.hide()
            self.commit_button.hide()
            self.add_new_row.hide()
        else:
            self.tips_label.hide()
            self.paste_button.show()
            self.commit_button.show()
            self.add_new_row.show()
        self._get_detail_table_data()

    def _get_detail_table_data(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/'
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            pass
        else:
            table_records = response['records']
            table_headers = table_records.pop(0)
            del table_headers['id']
            del table_headers['create_time']
            del table_headers['update_time']
            table_headers = [header for header in table_headers.values()]
            if self.option == 'modify':
                self._set_row_contents(table_headers, table_records)
            else:
                self._set_table_headers(table_headers)

    def _set_row_contents(self, headers, contents):
        headers.append('')
        columns = len(headers)
        self.table.setColumnCount(columns)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(contents))
        for row, row_item in enumerate(contents):
            for col in range(columns):
                if col == columns - 1:
                    item = QTableWidgetItem("修改这行")
                else:
                    key = 'column_{}'.format(col)
                    item = QTableWidgetItem(row_item[key])
                    if col == 0:
                        item.id = row_item['id']
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def _set_table_headers(self, headers):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def table_cell_clicked(self, row, col):
        if self.option != 'modify':
            return
        if col != self.table.columnCount() - 1:
            return
        record_id = self.table.item(row, 0).id
        record_content = list()
        for col_index in range(self.table.columnCount() - 1):
            record_content.append(self.table.item(row, col_index).text())
        # 发起修改请求
        try:
            r = requests.put(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/',
                headers={'Content-Type':'application/json;charset=utf8'},
                data=json.dumps({
                    'utoken': settings.app_dawn.value("AUTHORIZATION"),
                    'record_id': record_id,
                    'record_content': record_content
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '失败', response['message'])
        else:
            QMessageBox.information(self, '成功', response['message'])

    def paste_new_data(self):
        clipboard = QApplication.clipboard()  # 获取当前剪贴板的内容
        contents = re.split(r'\n', clipboard.text())  # 处理数据
        for row, row_item in enumerate(contents):
            row_content = re.split('\t', row_item)
            if not row_content[0]:
                continue
            self.table.insertRow(self.table.rowCount())
            for col, item_text in enumerate(row_content):
                if col > self.table.columnCount() - 1:
                    continue
                item = QTableWidgetItem(item_text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def _table_values(self):
        headers = list()
        contents = list()
        for col in range(self.table.columnCount()):
            headers.append(self.table.horizontalHeaderItem(col).text())
        for row in range(self.table.rowCount()):
            row_content = list()
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if not item:
                    break
                else:
                    row_content.append(item.text())
            if not row_content:
                continue
            try:
                # 判断第一列的数据格式得是日期的
                row_content[0] = datetime.datetime.strptime(row_content[0],'%Y-%m-%d').strftime('%Y-%m-%d')
            except Exception as e:
                QMessageBox.information(self, '错误','第{}行第1列日期格式错误.\n需为"YYYY-MM-DD"'.format(row + 1))
                contents.clear()
                break
            else:
                if len(row_content) != len(headers):
                    QMessageBox.information(self, '错误','您有空列未填写...')
                    contents.clear()
                else:
                    contents.append(row_content)
        return {
            'headers': headers,
            'contents': contents
        }

    def add_new_row_record(self):
        self.table.insertRow(self.table.rowCount())

    def commit_new_contents(self):
        self.commit_button.setEnabled(False)
        try:
            values = self._table_values()
            if len(values['contents']) <= 0:
                return
            r = requests.post(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/',
                headers={'Content-Type':'application/json;charset=utf8'},
                data=json.dumps({
                    'utoken': settings.app_dawn.value('AUTHORIZATION'),
                    'new_header': values['headers'],
                    'new_contents': values['contents']
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '失败', str(e))
        else:
            self.table.clear()
            QMessageBox.information(self, '成功', response['message'])
        finally:
            self.commit_button.setEnabled(True)


# 显示当前的数据表和支持管理操作
class InformationTable(QTableWidget):
    def __init__(self, *args):
        super(InformationTable, self).__init__(*args)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.doubleClicked.connect(self.enter_draw_charts)
        self.setObjectName('informationTable')
        self.setStyleSheet("""
        #informationTable{
            background-color:rgb(240,240,240);
            font-size: 13px;
            selection-color: rgb(180,60,60);
            selection-background-color: rgb(220,220,220);
            alternate-background-color: rgb(245, 250, 248);
        }
        """)

    def mousePressEvent(self, event):
        if event.buttons() == Qt.RightButton:
            index = self.indexAt(QPoint(event.x(), event.y()))
            current_row = index.row()
            self.setCurrentIndex(index)
            if current_row < 0:
                return
            menu = QMenu()
            charts_action = menu.addAction("进入绘图")
            charts_action.triggered.connect(self.enter_draw_charts)
            modify_action = menu.addAction("修改记录")
            modify_action.triggered.connect(self.modify_record)
            add_action = menu.addAction("增加记录")
            add_action.triggered.connect(self.add_new_records)
            delete_action = menu.addAction("删      除")
            delete_action.triggered.connect(self.delete_table)
            menu.exec_(QCursor.pos())
        else:
            super(InformationTable, self).mousePressEvent(event)

    def modify_record(self):
        current_row = self.currentRow()
        table_id = self.item(current_row, 0).id
        table_name = self.item(current_row, 1).text()
        popup = TableDetailRecordOpts(table_id=table_id,option='modify', parent=self.parent())
        popup.setWindowTitle("修改【" + table_name + "】")
        popup.exec_()

    def add_new_records(self):
        current_row = self.currentRow()
        table_id = self.item(current_row, 0).id
        table_name = self.item(current_row, 1).text()
        popup = TableDetailRecordOpts(table_id=table_id, option='add', parent=self.parent())
        popup.setWindowTitle("新增【" + table_name + "】")
        popup.exec_()

    def enter_draw_charts(self):
        current_row = self.currentRow()
        table_id = self.item(current_row, 0).id
        table_name = self.item(current_row, 1).text()
        variety_id = self.item(current_row, 0).variety_id
        popup = DrawChartsDialog(table_id=table_id, variety_id=variety_id, parent=self.parent())
        popup.setWindowTitle("【" + table_name + "】绘图")
        popup.show()

    def delete_table(self):
        """删除当前数据表"""
        table_id = self.item(self.currentRow(), 0).id
        if QMessageBox.Yes == QMessageBox.warning(self, '注意', '删除后与之关联的图表都将删除。\n您确定清除这张表吗?', QMessageBox.Yes|QMessageBox.No, QMessageBox.No):
            try:
                r = requests.delete(
                    url=settings.SERVER_ADDR + 'trend/table/' + str(table_id) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(self, '错误', str(e))
            else:
                QMessageBox.information(self, '成功', response['message'])
                self.removeRow(self.currentRow())

    def show_contents(self, row_contents):
        self.clear()
        table_headers = ["序号", '标题', '创建日期', '创建者', '最近更新','更新者']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_contents))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for row, row_item in enumerate(row_contents):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.variety_id = row_item['variety_id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['title'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['create_time'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['author'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['update_time'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['updater'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)


# 管理我的数据表
class UpdateTrendTablePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(UpdateTrendTablePage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(1, 1, 0, 0))
        opts_layout = QHBoxLayout(self)
        opts_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.currentTextChanged.connect(self._get_trend_group)
        opts_layout.addWidget(self.variety_combobox)
        opts_layout.addWidget(QLabel("数据组:", self))
        self.group_combobox = QComboBox(self)
        self.group_combobox.currentTextChanged.connect(self._get_current_tables)
        opts_layout.addWidget(self.group_combobox)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)
        self.trend_table = InformationTable(self)
        layout.addWidget(self.trend_table)
        self.setLayout(layout)

        self._get_access_varieties()

    def _get_access_varieties(self):
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.get(url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/variety/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            return []
        else:
            self.variety_combobox.clear()
            for variety_item in response['variety']:
                if variety_item['is_active']:
                    self.variety_combobox.addItem(variety_item['name'], variety_item['variety_id'])

    def _get_trend_group(self):
        current_variety_id = self.variety_combobox.currentData()
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'trend/group/?variety=' + str(current_variety_id),
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.group_combobox.clear()
            self.group_combobox.addItem("全部", 0)
            for group_item in response['groups']:
                self.group_combobox.addItem(group_item['name'], group_item['id'])

    def _get_current_tables(self):
        current_group_id = self.group_combobox.currentData()
        current_variety_id = self.variety_combobox.currentData()
        if current_group_id is None or current_variety_id is None:
            return
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'variety/' + str(current_variety_id) + '/trend/table/?group=' + str(current_group_id)
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            self.trend_table.show_contents(response['tables'])


# 更新数据组的线程
class UpdateVarietyTableGroupThread(QThread):
    process_finished = pyqtSignal(int, int)
    updating = pyqtSignal(int)

    def __init__(self, variety_id,group_id,file_folder, *args,**kwargs):
        super(UpdateVarietyTableGroupThread, self).__init__(*args, **kwargs)
        self.variety_id = variety_id
        self.group_id = group_id
        self.file_folder = file_folder
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.time_out)
        self.index = -1

    def time_out(self):
        if self.index < 3:
            self.index += 1
        else:
            self.index = 0
        self.updating.emit(self.index)

    def run(self):
        # 读取文件夹内所有文件
        file_path_list = list()
        for file_path in os.listdir(self.file_folder):
            if os.path.splitext(file_path)[1] in ['.xlsx', '.xls']:
                file_path_list.append(os.path.join(self.file_folder, file_path))
        # 遍历将每个文件和文件内的sheet，读取，发起更新或创建，提交后发出一个信号
        for file_path in file_path_list:
            try:
                file = xlrd.open_workbook(file_path)
            except Exception as e:
                settings.logger.error("打开文件:{}失败:{}".format(file_path, e))
                continue
            for sheet_name in file.sheet_names():
                time.sleep(0.3)
                try:
                    sheet = file.sheet_by_name(sheet_name)
                    if not file.sheet_loaded(sheet_name) or sheet.nrows < 4:  # 读取失败就继续，或是空数据表
                        continue
                    headers = sheet.row_values(1)  # 第一行读取，即表格中第二行
                    if len(headers) <= 0:  # 无读到表头，跳过这个sheet
                        continue
                    unit_row = sheet.row_values(2)  # 表格中第3行,默认为单位行或者其他信息行
                    # 处理与表头格式相同
                    if len(unit_row) <= 0:
                        unit_row = ['' for _ in range(len(headers))]
                    # print('表名:', sheet_name)
                    # print('读取到表格中第3行的数据:', unit_row)
                    contents = [headers, unit_row]
                    for row in range(3, sheet.nrows):  # 读取表格数据(从第4行开始读取具体信息)
                        row_content = []
                        if sheet.cell(row, 0).ctype == 3 and sheet.cell_value(row, 0) == 0:  # 如果这行是1900年，跳过
                            continue
                        for col in range(sheet.ncols):
                            cell_type = sheet.cell(row, col).ctype
                            if col == 0 and cell_type != 3:  # 第一列不是时间类型的，忽略本行数据（非时间行跳过）
                                # print("读取到非时间数据行:", row, col)
                                break
                            cell_value = sheet.cell_value(row, col)
                            if cell_type == 3:  # 时间列数据转为时间格式
                                cell_value = datetime.datetime(*xlrd.xldate_as_tuple(cell_value, 0)).strftime("%Y-%m-%d")
                            row_content.append(cell_value)
                        if len(row_content) == len(headers):  # 与表头同样大小
                            contents.append(row_content)
                except Exception as e:
                    settings.logger.error("打开'{}'文件下的'{}'表失败:{}".format(os.path.splitext(file_path)[0], sheet_name, e))
                    continue
                # 发起请求向服务器增加或更新数据
                # print('上传或更新数据:',file_path, sheet_name)
                self.send_data_to_server(
                    variety_id=self.variety_id,
                    group_id=self.group_id,
                    title=sheet_name,
                    table_values=contents
                )
            file.release_resources()  # 释放资源
            del file
        # 全部完成执行完成后，发出完成的信号True
        # self.timer.stop()
        self.process_finished.emit(self.variety_id, self.group_id)

    def send_data_to_server(self, variety_id, group_id, title, table_values):
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.post(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/trend/table/',
                headers={'Content-type': 'application/json;charset=utf8'},
                data=json.dumps({
                    'utoken': settings.app_dawn.value('AUTHORIZATION'),
                    'variety_id': variety_id,
                    'group_id': group_id,
                    'title': title,
                    'table_values':table_values
                })
            )
            if r.status_code not in [200, 201]:
                response = json.loads(r.content.decode('utf8'))
                raise ValueError(response['message'])
        except Exception as e:
            settings.logger.error("上传数据出错:{}".format(e))


# 配置数据源、更新数据的窗口
class UpdateTableConfigPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(UpdateTableConfigPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(1, 1, 0, 0))

        options_layout = QHBoxLayout(self)
        options_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.currentTextChanged.connect(self._read_configs)
        options_layout.addWidget(self.variety_combobox)
        options_layout.addWidget(QLabel("数据组:", self))
        self.vtable_group = QComboBox(self)
        options_layout.addWidget(self.vtable_group)
        # 新增数据组
        self.add_new_tgroup = QPushButton("新建组?", self, clicked=self.create_new_group)
        options_layout.addWidget(self.add_new_tgroup)
        options_layout.addStretch()

        self.new_config_button = QPushButton('配置', self)
        self.new_config_button.clicked.connect(self.add_new_update_config)
        options_layout.addWidget(self.new_config_button)
        layout.addLayout(options_layout)
        self.config_table = QTableWidget(self)
        self.config_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.config_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.config_table.setFrameShape(QFrame.NoFrame)
        self.config_table.setAlternatingRowColors(True)
        self.config_table.cellClicked.connect(self.config_table_cell_clicked)
        layout.addWidget(self.config_table)
        self.setLayout(layout)
        self.config_table.setObjectName('configsTable')
        self.setStyleSheet("""
        #configsTable{
            background-color:rgb(240,240,240);
            font-size: 13px;
            selection-color: rgb(180,60,60);
            alternate-background-color: rgb(245, 250, 248);
        }
        """)
        tips = "<p>1 点击右上角'配置'按钮，配置数据组文件所在的文件夹.</p>" \
               "<p>2 '点击更新'让系统读取文件夹内的数据表自动上传.</p>" \
               "<p>2-1 文件夹内表格格式:</p>" \
               "<p>第1行：万得导出的表第一行不动;自己创建的表第一行可留空;</p>" \
               "<p>第2行：数据表表头;</p>" \
               "<p>第3行：不做限制,可填入单位等,也可直接留空.</p>" \
               "<p>第4行：数据起始行,第一列为【日期】类型,非日期的行系统不会做读取.</p>"
        tips_label = QLabel(tips, self)
        tips_label.setStyleSheet("font-size:15px;color:rgb(180,100,100)")
        tips_label.setWordWrap(True)
        layout.addWidget(tips_label)
        self._get_access_variety()
        self._get_current_v_group()

    def _get_access_variety(self):
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.get(url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/variety/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            return []
        else:
            self.variety_combobox.clear()
            for variety_item in response['variety']:
                if variety_item['is_active']:
                    self.variety_combobox.addItem(variety_item['name'], variety_item['variety_id'])

            return response['variety']

    def _get_current_v_group(self):
        """获取当前品种数据组"""
        try:
            current_vid = self.variety_combobox.currentData()
            r = requests.get(url=settings.SERVER_ADDR + 'trend/group/?variety=' + str(current_vid))
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            self.vtable_group.clear()
            for group_item in response['groups']:
                self.vtable_group.addItem(group_item['name'], group_item['id'])

    # 读取当前的配置
    def _read_configs(self):
        self._get_current_v_group()
        self.config_table.clear()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels(['品种', '数据组', '数据文件夹', '上次更新',''])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.config_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        configs = self.get_current_configs()
        self.config_table.setRowCount(len(configs))
        for row,item in enumerate(configs):
            item0 = QTableWidgetItem(item['variety_name'])
            item0.variety_id = item['variety_id']
            item0.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(item['group_name'])
            item1.group_id = item['group_id']
            item1.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 1, item1)
            item2 = QTableWidgetItem(item['file_folder'])
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setToolTip(item['file_folder'])
            self.config_table.setItem(row, 2, item2)
            item3 = QTableWidgetItem(item['update_time'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 3, item3)
            item4 = QTableWidgetItem('点击更新')
            item4.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 4, item4)

    # 获取当前的配置
    def get_current_configs(self):
        current_variety = self.variety_combobox.currentData()
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/data_configs/',
                headers={'Content-Type':'application/json;charset=utf8', 'User-Agent': settings.USER_AGENT},
                data=json.dumps({
                    'utoken': settings.app_dawn.value('AUTHORIZATION'),
                    'machine_code': settings.app_dawn.value('machine'),
                    'variety_id': current_variety
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            return []
        else:
            return response['configs']

    def create_new_group(self):
        current_variety_name = self.variety_combobox.currentText()
        current_variety_id = self.variety_combobox.currentData()

        def commit_group_name():
            try:
                r = requests.post(
                    url=settings.SERVER_ADDR + 'trend/group/',
                    headers={"Content-Type":"application/json;charset=utf8"},
                    data=json.dumps({
                        'utoken':settings.app_dawn.value("AUTHORIZATION"),
                        'variety_id':current_variety_id,
                        'name': name_edit.text().strip()
                    })
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 201:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(popup, "错误", str(e))
            else:
                QMessageBox.information(popup, "成功", "成功添加数据组")
                popup.close()
                self._get_current_v_group()  # 动态刷新当前数据组
        if not current_variety_name or not current_variety_id:
            QMessageBox.information(self, "未选择品种", "请选择品种")
            return

        popup = QDialog(self)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.setWindowTitle("增加【" + current_variety_name + "】数据组")
        popup.setFixedSize(250, 80)
        layout = QVBoxLayout(popup)
        name_layout = QHBoxLayout(popup)
        name_layout.addWidget(QLabel("名称:", popup))
        name_edit = QLineEdit(popup)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        commit_btn = QPushButton("确定", popup)
        commit_btn.clicked.connect(commit_group_name)
        layout.addWidget(commit_btn, alignment=Qt.AlignRight)
        popup.setLayout(layout)
        popup.exec_()

    def add_new_update_config(self):
        def choose_file_folder():  # 选择文件夹
            folder = QFileDialog.getExistingDirectory()
            if not folder:
                return
            folder_path.setText(folder + '/')

        def add_new_config():
            current_vid = variety_combobox.currentData()
            current_vname = variety_combobox.currentText()
            current_gname = group_combobox.currentText()
            current_gid = group_combobox.currentData()
            current_folder = folder_path.text()
            if not current_folder:
                return
            new_config = {
                'machine_code': settings.app_dawn.value('machine'),
                'utoken': settings.app_dawn.value('AUTHORIZATION'),
                'variety_name': current_vname,
                'variety_id': current_vid,
                'group_name': current_gname,
                'group_id': current_gid,
                'file_folder': current_folder
            }
            try:
                r = requests.post(
                    url=settings.SERVER_ADDR + 'user/data_configs/',
                    headers={'Content-Type':'application/json;charset=utf8', 'User-Agent': settings.USER_AGENT},
                    data=json.dumps(new_config)
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(popup, '错误', str(e))
            else:
                QMessageBox.information(popup, '成功', response['message'])
                popup.close()

        def get_current_trend_group():
            # 获取当前品种数据组
            try:
                current_vid = variety_combobox.currentData()
                r = requests.get(url=settings.SERVER_ADDR + 'trend/group/?variety=' + str(current_vid))
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception:
                pass
            else:
                group_combobox.clear()
                for group_item in response['groups']:
                    group_combobox.addItem(group_item['name'], group_item['id'])

        popup = QDialog(self.parent())
        popup.setWindowTitle("配置路径")
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.setFixedSize(320, 160)
        layout = QGridLayout(popup)
        layout.addWidget(QLabel("品种:", popup), 0, 0)
        variety_combobox = QComboBox(popup)
        variety_combobox.currentTextChanged.connect(get_current_trend_group)

        layout.addWidget(variety_combobox, 0, 1, 1, 2)
        group_combobox = QComboBox(popup)
        layout.addWidget(QLabel('数据组'), 1, 0)
        layout.addWidget(group_combobox, 1, 1,1,2)
        for variety_item in self._get_access_variety():
            if variety_item['is_active']:
                variety_combobox.addItem(variety_item['name'], variety_item['variety_id'])
        layout.addWidget(QLabel('路径:', popup), 2, 0)
        folder_path = QLineEdit(popup)
        layout.addWidget(folder_path, 2, 1)
        button = QPushButton('选择', popup)
        button.clicked.connect(choose_file_folder)
        layout.addWidget(button, 2, 2)
        add_config = QPushButton('确定添加',popup)
        add_config.clicked.connect(add_new_config)
        layout.addWidget(add_config, 3, 0, 1, 3)
        popup.setLayout(layout)
        if not popup.exec_():
            self._read_configs()

    def config_table_cell_clicked(self, row, col):
        updating_text = ['正在更新 ', '在更新 正', '更新 正在', '新 正在更']
        current_text = self.config_table.item(row, 4).text()
        if col != 4 or current_text != '点击更新':
            return

        def process_finished(variety_id, group_id):  # 更新结束
            self.update_thread.timer.stop()
            self.config_table.item(row, 4).setText('更新完成')
            self.update_thread.deleteLater()
            del self.update_thread
            # 更新时间修改
            try:
                requests.patch(
                    url=settings.SERVER_ADDR + 'user/data_configs/',
                    headers={'Content-Type':'application/json;charset=utf8', 'User-Agent': settings.USER_AGENT},
                    data=json.dumps({
                        'utoken': settings.app_dawn.value('AUTHORIZATION'),
                        'machine_code': settings.app_dawn.value('machine'),
                        'variety_id': variety_id,
                        'group_id': group_id
                    })
                )
            except Exception:
                pass
            else:
                self.config_table.item(row, 3).setText(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        def updating_show(index):  # 提示正在更新
            self.config_table.item(row, 4).setText(updating_text[index])
        variety_id = self.config_table.item(row, 0).variety_id
        group_id = self.config_table.item(row, 1).group_id
        file_folder = self.config_table.item(row, 2).text()
        # 开启线程更新数据
        self.update_thread = UpdateVarietyTableGroupThread(variety_id,group_id,file_folder)
        self.update_thread.updating.connect(updating_show)
        self.update_thread.process_finished.connect(process_finished)
        self.update_thread.timer.start(700)  # 开启提示
        self.update_thread.start()


# 管理我的数据图
class MyTrendChartTableManage(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(MyTrendChartTableManage, self).__init__(*args)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setObjectName("chartManageTable")
        self.setStyleSheet("""
        #chartManageTable{
            background-color:rgb(240,240,240);
            font-size: 13px;
            selection-color: rgb(180,60,60);
            election-background-color: rgb(220,220,220);
            alternate-background-color: rgb(245, 250, 248);
        }
        """)

    def mousePressEvent(self, event):
        if event.buttons() == Qt.RightButton:
            index = self.indexAt(QPoint(event.x(), event.y()))
            current_row = index.row()
            self.setCurrentIndex(index)
            if current_row < 0:
                return
            is_trend_show = self.item(current_row, 0).is_trend_show
            is_variety_show = self.item(current_row, 0).is_variety_show
            menu = QMenu()

            edit_decipherment_action = menu.addAction("编辑解说")
            edit_decipherment_action.triggered.connect(self.edit_decipherment)

            trend_show_action = menu.addAction('首页显示')
            if is_trend_show:
                trend_show_action.setIcon(QIcon('media/checked.png'))
            trend_show_action.triggered.connect(self.chart_show_in_trend)

            variety_show_action = menu.addAction('品种显示')
            if is_variety_show:
                variety_show_action.setIcon(QIcon('media/checked.png'))
            variety_show_action.triggered.connect(self.chart_show_in_variety)
            delete_action = menu.addAction('删除图表')
            delete_action.triggered.connect(self.delete_chart)

            menu.exec_(QCursor.pos())
        else:
            super(MyTrendChartTableManage, self).mousePressEvent(event)

    # 首页显示,品种页显示和解说修改
    def modify_chart_information(self):
        item0 = self.item(self.currentRow(), 0)
        chart_id = item0.id
        is_trend_show = item0.is_trend_show
        is_variety_show = item0.is_variety_show
        decipherment = self.item(self.currentRow(), 4).text()
        try:
            r = requests.patch(
                url=settings.SERVER_ADDR + 'trend/table-chart/' + str(chart_id) + '/',
                headers={'Content-Type': 'application/json;charset=utf8', "User-Agent": settings.USER_AGENT},
                data=json.dumps({
                    "utoken": settings.app_dawn.value("AUTHORIZATION"),
                    "decipherment": decipherment,
                    "is_trend_show": is_trend_show,
                    "is_variety_show": is_variety_show
                })
            )
            response = json.loads(r.content.decode("utf-8"))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
            return False
        else:
            QMessageBox.information(self, '成功', response['message'])
            return True

    # 首页显示
    def chart_show_in_trend(self):
        item0 = self.item(self.currentRow(), 0)
        item0.is_trend_show = not item0.is_trend_show
        self.modify_chart_information()

    # 品种显示
    def chart_show_in_variety(self):
        item0 = self.item(self.currentRow(), 0)
        item0.is_variety_show = not item0.is_variety_show
        self.modify_chart_information()

    # 编辑解说
    def edit_decipherment(self):
        decipherment = self.item(self.currentRow(), 4).text()

        def upload_decipherment():
            text = text_edit.toPlainText()
            decipherment_item = self.item(self.currentRow(), 4)
            decipherment_item.setText(text)
            if self.modify_chart_information():
                popup.close()
        popup = QDialog(self)
        popup.setWindowTitle("编辑图形解说")
        popup.resize(400, 200)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(popup)
        text_edit = QTextEdit(decipherment, popup)
        layout.addWidget(text_edit)
        confirm = QPushButton('确定',popup)
        confirm.clicked.connect(upload_decipherment)
        layout.addWidget(confirm, alignment=Qt.AlignRight)
        popup.setLayout(layout)
        popup.show()

    # 删除数据图形
    def delete_chart(self):
        chart_id = self.item(self.currentRow(), 0).id
        if QMessageBox.Yes == QMessageBox.warning(self, '提醒', '删除将无法恢复?', QMessageBox.Yes|QMessageBox.No):
            try:
                utoken = settings.app_dawn.value('AUTHORIZATION')
                r = requests.delete(
                    url=settings.SERVER_ADDR + 'trend/table-chart/' + str(chart_id) + '/?utoken=' + utoken
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(self, '失败', str(e))
            else:
                QMessageBox.information(self, '成功', '删除成功')
                self.removeRow(self.currentRow())

    # 显示图形信息
    def show_charts_info(self, contents):
        table_headers = ['序号','标题', '创建时间', '更新时间', '图形解说', '图形']
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(table_headers)
        self.setRowCount(len(contents))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(contents):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.is_trend_show = row_item['is_trend_show']
            item0.is_variety_show = row_item['is_variety_show']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['title'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['create_time'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['update_time'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['decipherment'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            btn = QPushButton(self)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(QIcon('media/nor_chart.png'))
            btn.chart_id = row_item['id']
            btn.clicked.connect(self.view_chart_show)
            self.setCellWidget(row, 5, btn)

    def view_chart_show(self):
        QMessageBox.information(self, "提示", '单独查看图形正在开发中...\n请在【图形总览】选项中查看.')
        # button = self.sender()
        # chart_id = button.chart_id
        # print(chart_id)


# 显示我的数据图
class MyTrendTableChartPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(MyTrendTableChartPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(QMargins(1, 1, 0, 0))
        opts_layout = QHBoxLayout(self)
        opts_layout.addWidget(QLabel('品种:', self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.currentTextChanged.connect(self.get_current_charts_info)
        opts_layout.addWidget(self.variety_combobox)
        self.switchover = QPushButton("图形管理", self)
        self.switchover.clicked.connect(self.switch_show_widget)
        opts_layout.addWidget(self.switchover)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # onload show charts page
        self.show_charts = QWebEngineView(self)
        layout.addWidget(self.show_charts)

        self.manage_table = MyTrendChartTableManage(self)
        layout.addWidget(self.manage_table)
        self.manage_table.hide()
        self.setLayout(layout)
        # self.show_charts.page().loadFinished.connect(self._get_accessed_variety)
        self._get_accessed_variety()

    def _get_accessed_variety(self):
        # 获取有权限的品种信息
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.get(settings.SERVER_ADDR + 'user/' + str(user_id) + '/variety/')
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            pass
        else:
            self.variety_combobox.clear()
            self.variety_combobox.addItem('全部', 0)
            accessed_variety = response['variety']
            for variety_item in accessed_variety:
                self.variety_combobox.addItem(variety_item['name'], variety_item['variety_id'])

    def switch_show_widget(self):
        if self.manage_table.isHidden():
            self.show_charts.hide()
            self.manage_table.show()
            self.switchover.setText('图形总览')
        else:
            self.show_charts.show()
            self.manage_table.hide()
            self.switchover.setText('图形管理')
        self.get_current_charts_info()

    # 获取所有表的信息传入页面
    def get_current_charts_info(self):
        current_variety = self.variety_combobox.currentData()
        user_id = pickle.loads(settings.app_dawn.value('UKEY'))
        if self.manage_table.isHidden():
            self.show_charts.load(QUrl(settings.SERVER_ADDR + 'trend/table-chart/?vid=' + str(current_variety) + '&utoken=' + settings.app_dawn.value("AUTHORIZATION")))
        else:
            # 请求当前用户的所有表信息
            try:
                r = requests.get(
                    url=settings.SERVER_ADDR + 'trend/table-chart/?vid=' + str(current_variety) + '&utoken=' + settings.app_dawn.value("AUTHORIZATION") + "&is_json=1"
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                settings.logger.error("获取图形表信息失败:{}".format(e))
            else:
                self.manage_table.show_charts_info(response['charts'])


class BaseTrendAdmin(QWidget):
    def __init__(self, *args, **kwargs):
        super(BaseTrendAdmin, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        # 左侧管理菜单列表
        self.left_list = QListWidget(parent=self, clicked=self.left_list_clicked)
        layout.addWidget(self.left_list, alignment=Qt.AlignLeft)
        # 右侧显示的frame
        self.frame_loaded = LoadedPage(self)
        self.frame_loaded.remove_borders()
        layout.addWidget(self.frame_loaded)
        self.setLayout(layout)

        self.left_list.setObjectName('leftList')
        self.setStyleSheet("""
        #leftList{
            outline:none;
            border:none;
            border-right: 1px solid rgb(180,180,180);
            background-color: rgb(240,240,240);
        }
        #leftList::item{
           height:25px;
        }
        #leftList::item:selected{
           border-left:3px solid rgb(100,120,150);
           color:#000;
           background-color:rgb(180,220,230);
        }
        """)

    def add_left_menus(self):
        for item in [u'数据源配置', u'品种数据表', u'我的数据图']:
            self.left_list.addItem(QListWidgetItem(item))

    def left_list_clicked(self):
        text = self.left_list.currentItem().text()
        if text == u'品种数据表':
            frame_page = UpdateTrendTablePage(parent=self)
        elif text == u'数据源配置':
            frame_page = UpdateTableConfigPage(parent=self)
        elif text == u'我的数据图':
            frame_page = MyTrendTableChartPage(parent=self)
        else:
            frame_page = QLabel('【' + text + '】正在加紧开发中...')
        self.frame_loaded.clear()
        self.frame_loaded.addWidget(frame_page)

