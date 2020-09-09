# _*_ coding:utf-8 _*_
# @File  : industry_popup.py
# @Time  : 2020-09-03 20:30
# @Author: zizle
""" 行业数据的弹窗U组件 """
import os
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from PyQt5.QtWidgets import (qApp, QDesktopWidget, QDialog, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QSplitter, QLineEdit, QSpinBox, QComboBox, QGroupBox, QTableWidget, QCheckBox,
                             QListWidget, QListWidgetItem, QTableWidgetItem, QHeaderView, QMenu, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMargins, QUrl
from PyQt5.QtGui import QBrush, QColor, QIntValidator
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebChannel import QWebChannel
from widgets.path_edit import FolderPathLineEdit
from widgets.cover import CoverWidget
from channels.chart import ChartOptionChannel
from utils.client import get_client_uuid, get_user_token
from settings import BASE_DIR, SERVER_API, logger


class UpdateFolderPopup(QDialog):
    """ 更新数据的文件夹配置 """
    successful_signal = pyqtSignal(str)

    def __init__(self, variety_en, variety_text, group_id, group_text, *args, **kwargs):
        super(UpdateFolderPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.variety_en = variety_en
        self.group_id = group_id

        self.setWindowTitle("配置「" + variety_text + "」的更新路径")

        main_layout = QGridLayout()

        main_layout.addWidget(QLabel("品种:", self), 0, 0)
        main_layout.addWidget(QLabel(variety_text, self), 0, 1)

        main_layout.addWidget(QLabel("组别:"), 1, 0)
        main_layout.addWidget(QLabel(group_text), 1, 1)

        main_layout.addWidget(QLabel("路径:"), 2, 0)
        self.folder_edit = FolderPathLineEdit(self)
        main_layout.addWidget(self.folder_edit)

        self.confirm_button = QPushButton("确定", self)
        self.confirm_button.clicked.connect(self.confirm_current_folder)
        main_layout.addWidget(self.confirm_button, 3, 1, alignment=Qt.AlignRight)

        self.setLayout(main_layout)
        self.setMinimumWidth(370)
        self.setFixedHeight(155)

    def confirm_current_folder(self):
        """ 确定当前配置 """
        # 打开sqlite3进行数据的保存
        folder_path = self.folder_edit.text()
        if not folder_path:
            return
        insert_data = [get_client_uuid(), self.variety_en, self.group_id, folder_path]
        db_path = os.path.join(BASE_DIR, "dawn/local_data.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT CLIENT,VARIETY_EN,GROUP_ID FROM UPDATE_FOLDER "
            "WHERE CLIENT=? AND VARIETY_EN=? AND GROUP_ID=?;",
            (insert_data[0], insert_data[1], insert_data[2])
        )
        if cursor.fetchone():  # 更新
            cursor.execute(
                "UPDATE UPDATE_FOLDER SET FOLDER=? "
                "WHERE CLIENT=? AND VARIETY_EN=? AND GROUP_ID=?;",
                (insert_data[3], insert_data[0], insert_data[1], insert_data[2])
            )
        else:  # 新建
            cursor.execute(
                "INSERT INTO UPDATE_FOLDER (CLIENT,VARIETY_EN,GROUP_ID,FOLDER) "
                "VALUES (?,?,?,?);",
                insert_data
            )
        conn.commit()
        cursor.close()
        conn.close()
        self.successful_signal.emit("调整配置成功!")


""" 图形配置选项 """


class OptionWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(OptionWidget, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:", self))
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("图形标题(保存配置时必填)")
        title_layout.addWidget(self.title_edit)
        title_layout.addWidget(QLabel("大小:", self))
        self.title_fontsize = QSpinBox(self)
        self.title_fontsize.setMinimum(10)
        self.title_fontsize.setMaximum(100)
        self.title_fontsize.setValue(22)
        title_layout.addWidget(self.title_fontsize)
        main_layout.addLayout(title_layout)

        x_axis = QHBoxLayout()
        x_axis.addWidget(QLabel("横轴:", self))
        self.x_axis_combobox = QComboBox(self)
        self.x_axis_combobox.setMinimumWidth(150)
        x_axis.addWidget(self.x_axis_combobox)
        x_axis.addStretch()
        main_layout.addLayout(x_axis)

        x_format = QHBoxLayout()
        x_format.addWidget(QLabel("格式:", self))
        self.date_length = QComboBox(self)
        self.date_length.addItem('年-月-日', 10)
        self.date_length.addItem('年-月', 7)
        self.date_length.addItem('年', 4)
        self.date_length.setMinimumWidth(150)
        x_format.addWidget(self.date_length)
        x_format.addStretch()
        main_layout.addLayout(x_format)

        add_indicator = QGroupBox("点击选择添加指标", self)
        self.indicator_list = QListWidget(self)
        add_indicator_layout = QVBoxLayout()
        add_indicator.setLayout(add_indicator_layout)
        add_indicator_layout.addWidget(self.indicator_list)

        # 添加指标的按钮
        button_layout = QGridLayout()
        indicator_button1 = QPushButton("左轴线型", self)
        setattr(indicator_button1, "axis_index", 0)
        setattr(indicator_button1, "chart", "line")
        indicator_button1.clicked.connect(self.selected_indicator)
        button_layout.addWidget(indicator_button1, 0, 0)
        indicator_button2 = QPushButton("左轴柱型", self)
        setattr(indicator_button2, "axis_index", 0)
        setattr(indicator_button2, "chart", "bar")
        indicator_button2.clicked.connect(self.selected_indicator)
        button_layout.addWidget(indicator_button2, 1, 0)
        indicator_button3 = QPushButton("右轴线型", self)
        setattr(indicator_button3, "axis_index", 1)
        setattr(indicator_button3, "chart", "line")
        indicator_button3.clicked.connect(self.selected_indicator)
        button_layout.addWidget(indicator_button3, 0, 1)
        indicator_button4 = QPushButton("右轴柱型", self)
        setattr(indicator_button4, "axis_index", 1)
        setattr(indicator_button4, "chart", "bar")
        indicator_button4.clicked.connect(self.selected_indicator)
        button_layout.addWidget(indicator_button4, 1, 1)
        add_indicator_layout.addLayout(button_layout)
        main_layout.addWidget(add_indicator)

        current_indicator = QGroupBox("双击删除已选指标", self)
        current_indicator_layout = QVBoxLayout()
        current_indicator.setLayout(current_indicator_layout)
        self.current_indicator_list = QListWidget(self)
        self.current_indicator_list.itemDoubleClicked.connect(self.remove_selected_indicator)  # 移除已选指标
        self.current_indicator_list.itemClicked.connect(self.change_check_state)               # 修改去0选项
        current_indicator_layout.addWidget(self.current_indicator_list)
        main_layout.addWidget(current_indicator)

        # 水印
        graphic_layout = QHBoxLayout()
        graphic_layout.setSpacing(1)
        self.has_graphic = QCheckBox(self)
        self.has_graphic.setText("添加水印")
        self.water_graphic = QLineEdit(self)
        self.water_graphic.setText("瑞达期货研究院")
        graphic_layout.addWidget(self.has_graphic)
        graphic_layout.addWidget(self.water_graphic)
        graphic_layout.addStretch()
        main_layout.addLayout(graphic_layout)
        # 取数范围
        range_layout = QHBoxLayout()
        range_layout.setSpacing(1)
        self.start_year = QComboBox(self)
        self.end_year = QComboBox(self)
        self.range_check = QCheckBox(self)
        self.range_check.setText("取数范围")
        range_layout.addWidget(self.range_check)
        range_layout.addWidget(self.start_year)
        middle_label = QLabel("至", self)
        middle_label.setContentsMargins(QMargins(2, 0, 2, 0))
        range_layout.addWidget(middle_label)
        range_layout.addWidget(self.end_year)
        range_layout.addStretch()
        main_layout.addLayout(range_layout)

        other_layout = QHBoxLayout()
        tip_label = QLabel("勾选时,范围0表示不限制.", self)
        tip_label.setStyleSheet("color:rgb(180,60,60);max-height:15px")
        other_layout.addWidget(tip_label)
        self.more_dispose_button = QPushButton("更多配置", self)
        other_layout.addWidget(self.more_dispose_button, alignment=Qt.AlignRight)
        main_layout.addLayout(other_layout)

        draw_layout = QHBoxLayout()
        self.chart_drawer = QPushButton('确认绘图', self)
        setattr(self.chart_drawer, "chart_type", "normal")
        draw_layout.addWidget(self.chart_drawer)
        self.season_drawer = QPushButton('季节图表', self)
        setattr(self.season_drawer, "chart_type", "season")
        draw_layout.addWidget(self.season_drawer)
        main_layout.addLayout(draw_layout)

        self.setLayout(main_layout)

    def selected_indicator(self):
        """ 选择指标准备绘图 """
        current_indicator = self.indicator_list.currentItem()
        sender_button = self.sender()
        if not current_indicator:
            return
        indicator_column = current_indicator.data(Qt.UserRole)
        indicator_text = current_indicator.text()
        axis_index = getattr(sender_button, "axis_index")
        chart_type = getattr(sender_button, "chart")
        button_text = sender_button.text()
        indicator_params = {
            "column_index": indicator_column,
            "axis_index": axis_index,
            "chart_type": chart_type,
            "chart_name": indicator_text,
            "contain_zero": 1
        }
        # 重复指标和类型不再添加了
        for item_at in range(self.current_indicator_list.count()):
            item = self.current_indicator_list.item(item_at)
            exist_list = item.data(Qt.UserRole)
            if exist_list == indicator_params:
                return
        # 已选指标内添加指标
        selected_indicator_item = QListWidgetItem("(数据含0) " + indicator_text + " = " + button_text)
        selected_indicator_item.setCheckState(Qt.Unchecked)
        selected_indicator_item.setData(Qt.UserRole, indicator_params)
        self.current_indicator_list.addItem(selected_indicator_item)

    def remove_selected_indicator(self, _):
        """ 删除已选的指标 """
        current_row = self.current_indicator_list.currentRow()
        item = self.current_indicator_list.takeItem(current_row)
        del item

    @staticmethod
    def change_check_state(item):
        """ 修改item的去0选项"""
        text = item.text()
        if item.checkState():
            suffix_text = text[:6].replace("去", "含")
            indicator_params = item.data(Qt.UserRole)
            indicator_params["contain_zero"] = 1
            item.setCheckState(Qt.Unchecked)
        else:
            suffix_text = text[:6].replace("含", "去")
            indicator_params = item.data(Qt.UserRole)
            indicator_params["contain_zero"] = 0
            item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole, indicator_params)     # 重新设置item的Data
        text = suffix_text + text[6:]
        item.setText(text)

    def get_base_option(self):
        """ 图形的基本配置 """
        option = dict()
        # 标题
        option["title"] = {
            "text": self.title_edit.text().strip(),
            "font_size": self.title_fontsize.value()
        }
        # x轴
        option["x_axis"] = {
            "column_index": self.x_axis_combobox.currentData(),
            "date_length": self.date_length.currentData()
        }
        # y轴
        option["y_axis"] = [
            {"type": "value", "name": ""}
        ]
        # 数据序列
        series_data = []
        for item_at in range(self.current_indicator_list.count()):
            item = self.current_indicator_list.item(item_at)
            item_data = item.data(Qt.UserRole)
            if item_data["axis_index"] == 1 and len(option["y_axis"]) == 1:  # 如果有右轴添加右轴
                option["y_axis"].append({"type": "value", "name": ""})
            series_data.append(item_data)
        option["series_data"] = series_data

        option["watermark"] = ""
        if self.has_graphic.isChecked():
            option["watermark"] = self.water_graphic.text().strip()
        option["start_year"] = "0"
        option["end_year"] = "0"
        if self.range_check.isChecked():
            option["start_year"] = self.start_year.currentText()
            option["end_year"] = self.end_year.currentText()
        return option


class MoreDisposePopup(QDialog):
    """ 更多配置参数弹窗 """
    def __init__(self, *args, **kwargs):
        super(MoreDisposePopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("更多参数")
        integer_validate = QIntValidator(self)

        main_layout = QVBoxLayout()

        left_label = QLabel('左轴调整:', self)
        left_label.setObjectName("axisTile")
        main_layout.addWidget(left_label)
        left_unit_layout = QHBoxLayout()
        left_unit_layout.setContentsMargins(7, 0, 0, 0)
        left_unit_layout.addWidget(QLabel("名称:", self))
        self.left_name_edit = QLineEdit(self)
        left_unit_layout.addWidget(self.left_name_edit)

        left_unit_layout.addWidget(QLabel("最小值:", self))
        self.left_min_edit = QLineEdit(self)
        self.left_min_edit.setValidator(integer_validate)
        left_unit_layout.addWidget(self.left_min_edit)

        left_unit_layout.addWidget(QLabel("最大值:", self))
        self.left_max_edit = QLineEdit(self)
        self.left_max_edit.setValidator(integer_validate)
        left_unit_layout.addWidget(self.left_max_edit)

        left_unit_layout.addStretch()
        main_layout.addLayout(left_unit_layout)

        right_label = QLabel('右轴调整:', self)
        right_label.setObjectName("axisTile")
        main_layout.addWidget(right_label)
        right_unit_layout = QHBoxLayout()
        right_unit_layout.setContentsMargins(7, 0, 0, 0)
        right_unit_layout.addWidget(QLabel("名称:", self))
        self.right_name_edit = QLineEdit(self)
        right_unit_layout.addWidget(self.right_name_edit)

        right_unit_layout.addWidget(QLabel("最小值:", self))
        self.right_min_edit = QLineEdit(self)
        self.right_min_edit.setValidator(integer_validate)
        right_unit_layout.addWidget(self.right_min_edit)

        right_unit_layout.addWidget(QLabel("最大值:", self))
        self.right_max_edit = QLineEdit(self)
        self.right_max_edit.setValidator(integer_validate)
        right_unit_layout.addWidget(self.right_max_edit)

        right_unit_layout.addStretch()
        main_layout.addLayout(right_unit_layout)

        close_btn = QPushButton("确定", self)
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.setLayout(main_layout)
        self.setMaximumWidth(420)
        self.setStyleSheet(
            "#axisTile{padding:3px;font-size:14px;background:rgb(200,220,230);border-radius:3px}"
        )

    def get_more_option(self):
        """ 返回更多参数数据 """
        left_min = int(self.left_min_edit.text()) if self.left_min_edit.text() else None
        left_max = int(self.left_max_edit.text()) if self.left_max_edit.text() else None
        right_min = int(self.right_min_edit.text()) if self.right_min_edit.text() else None
        right_max = int(self.right_max_edit.text()) if self.right_max_edit.text() else None
        return {
            "left_axis": {
                "name": self.left_name_edit.text().strip(),
                "min_value": left_min,
                "max_value": left_max
            },
            "right_axis": {
                "name": self.right_name_edit.text().strip(),
                "min_value": right_min,
                "max_value": right_max
            }
        }


class ChartWidget(QWidget):
    """ 图形显示控件 """
    save_option_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(ChartWidget, self).__init__(*args, *kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        self.chart_container = QWebEngineView(self)
        self.chart_container.load(QUrl("file:///html/charts/custom_chart.html"))   # 加载页面
        # 设置与页面信息交互的通道
        channel_qt_obj = QWebChannel(self.chart_container.page())                  # 实例化qt信道对象,必须传入页面参数
        self.contact_channel = ChartOptionChannel()                                # 页面信息交互通道
        self.chart_container.page().setWebChannel(channel_qt_obj)
        channel_qt_obj.registerObject("pageContactChannel", self.contact_channel)  # 信道对象注册信道，只能注册一个

        main_layout.addWidget(self.chart_container)

        other_layout = QHBoxLayout()
        self.decipherment_edit = QLineEdit(self)
        self.decipherment_edit.setPlaceholderText("此处填写对图形的文字解读(非必填)")
        other_layout.addWidget(self.decipherment_edit)

        self.private_check = QCheckBox(self)
        self.private_check.setText("仅自己可见")
        other_layout.addWidget(self.private_check)

        save_button = QPushButton("保存图形", self)
        save_menu = QMenu(save_button)
        chart_action = save_menu.addAction("普通图形")
        setattr(chart_action, "chart_type", "normal")
        chart_action.triggered.connect(self.save_chart_option)
        season_action = save_menu.addAction("季节图形")
        setattr(season_action, "chart_type", "season")
        season_action.triggered.connect(self.save_chart_option)
        save_button.setMenu(save_menu)
        other_layout.addWidget(save_button)
        main_layout.addLayout(other_layout)

        self.setLayout(main_layout)

    def save_chart_option(self):
        """ 保存当前的图形配置 """
        action = self.sender()
        normal = getattr(action, "chart_type")
        self.save_option_signal.emit(normal)

    def show_chart(self, chart_type, option, values):
        """ 显示图形
        option:(json字符串)基础的图形配置,
        values:(json字符串)用于绘图的数据
        """
        self.contact_channel.chartSource.emit(chart_type, option, values)


class DisposeChartPopup(QDialog):
    """ 配置图形json信息进行绘图或保存 """

    def __init__(self, variety_en, sheet_id, *args, **kwargs):
        super(DisposeChartPopup, self).__init__(*args, **kwargs)
        self.source_dataframe = None

        # 更多配置弹窗
        self.more_dispose_popup = MoreDisposePopup(self)
        self.more_dispose_popup.close()

        # 初始化大小
        available_size = QDesktopWidget().availableGeometry()  # 用户的桌面信息,来改变自身窗体大小
        available_width, available_height = available_size.width(), available_size.height()
        self.resize(available_width * 0.65, available_height * 0.72)

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.variety_en = variety_en
        self.sheet_id = sheet_id

        main_layout = QHBoxLayout()
        main_splitter = QSplitter(self)
        main_layout.addWidget(main_splitter)  # 套layout自动改变大小

        self.option_widget = OptionWidget(self)
        self.option_widget.resize(self.width() * 0.4, self.height())
        self.option_widget.more_dispose_button.clicked.connect(self.show_more_dispose)
        main_splitter.addWidget(self.option_widget)

        chart_sheet_splitter = QSplitter(self)
        chart_sheet_splitter.setOrientation(Qt.Vertical)

        self.chart_widget = ChartWidget(self)
        self.chart_widget.save_option_signal.connect(self.save_option_to_server)  # 链接保存图形的信号
        chart_sheet_splitter.addWidget(self.chart_widget)

        self.sheet_table = QTableWidget(self)
        self.sheet_table.resize(self.width() * 0.6, self.height() * 0.4)
        self.sheet_table.verticalHeader().hide()
        chart_sheet_splitter.addWidget(self.sheet_table)

        chart_sheet_splitter.setStretchFactor(0, 4)
        chart_sheet_splitter.setStretchFactor(1, 6)
        main_splitter.addWidget(chart_sheet_splitter)

        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 6)

        self.setLayout(main_layout)

        # 遮罩层
        self.cover_widget = CoverWidget("正在加载数据 ")
        self.cover_widget.setParent(self)
        self.cover_widget.resize(self.width(), self.height())

        self._get_sheet_values()

        self.sheet_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 #bbbbbb, stop: 0.5 #eeeeee,stop: 0.6 #eeeeee, stop:1 #bbbbbb);"
            "border:1px solid rgb(201,202,202);border-left:none;"
            "min-height:25px;min-width:40px;font-weight:bold;font-size:13px};"
        )

        self.option_widget.chart_drawer.clicked.connect(self.preview_chart_with_option)        # 在右侧图形窗口显示图形信号
        self.option_widget.season_drawer.clicked.connect(self.preview_chart_with_option)       # 季节图形

    def resizeEvent(self, event):
        if not self.cover_widget.isHidden():
            self.cover_widget.resize(self.width(), self.height())

    def _get_sheet_values(self):
        """ 获取数据表的源数据 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "sheet/{}/".format(self.sheet_id)
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.sheet_values_reply)

    def sheet_values_reply(self):
        reply = self.sender()
        if reply.error():
            logger.error("用户获取数据表源数据失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            self.cover_widget.set_text(text="正在处理数据 ")
            # 使用pandas处理数据到弹窗相应参数中
            self.handler_sheet_values(data["sheet_values"])

    def handler_sheet_values(self, values):
        """ pandas处理数据到弹窗相应参数中 """
        value_df = pd.DataFrame(values)
        if value_df.iloc[2:].empty:                                             # 从第3行起取数,为空
            logger.error("该数据表最多存在3行数据,遂取绘图数据失败!")
            self.cover_widget.hide()
            return
        self.source_dataframe = value_df.copy()                                 # 将源数据复制一份关联到窗口(用于作图)
        sheet_headers = value_df.iloc[:1].to_numpy().tolist()[0]                # 取表头
        sheet_headers.pop(0)                                                    # 删掉id列
        col_index_list = ["id", ]
        for i, header_item in enumerate(sheet_headers):                         # 根据表头生成数据选择项
            col_index = "column_{}".format(i)
            self.option_widget.x_axis_combobox.addItem(header_item, col_index)  # 添加横轴选项
            indicator_item = QListWidgetItem(header_item)
            indicator_item.setData(Qt.UserRole, col_index)
            self.option_widget.indicator_list.addItem(indicator_item)           # 填入指标选择框
            col_index_list.append(col_index)
        # 根据最值填入起终值的范围
        max_date = value_df.iloc[2:]["column_0"].max()                          # 取日期最大值
        min_date = value_df.iloc[2:]["column_0"].min()                          # 取日期最小值
        self.option_widget.start_year.clear()
        self.option_widget.end_year.clear()
        self.option_widget.start_year.addItem("0")
        self.option_widget.end_year.addItem("0")
        for year in range(int(min_date[:4]), int(max_date[:4]) + 1):
            self.option_widget.start_year.addItem(str(year))
            self.option_widget.end_year.addItem(str(year))

        sheet_headers.insert(0, "编号")                                         # 还原id列
        self.sheet_table.setColumnCount(len(sheet_headers))
        self.sheet_table.setHorizontalHeaderLabels(sheet_headers)
        self.sheet_table.setRowCount(value_df.shape[0] - 1)
        self.sheet_table.horizontalHeader().setDefaultSectionSize(150)
        self.sheet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.sheet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        table_show_df = value_df.iloc[1:]
        table_show_df = table_show_df.sort_values(by="column_0")
        table_show_df.reset_index(inplace=True)                                  # 重置索引,让排序生效(赋予row正确的值)
        for row, row_item in table_show_df.iterrows():                           # 遍历数据(填入表格显示)
            for col, col_key in enumerate(col_index_list):
                # print(row_item[col_key], end=' ')
                item = QTableWidgetItem(str(row_item[col_key]))
                item.setTextAlignment(Qt.AlignCenter)
                if col < 2:
                    item.setFlags(Qt.ItemIsEditable)                            # ID,日期不可编辑
                    item.setForeground(QBrush(QColor(60, 60, 60)))
                self.sheet_table.setItem(row, col, item)
            # print()
        self.cover_widget.hide()

    def show_more_dispose(self):
        """ 更多的配置参数 """
        self.more_dispose_popup.exec_()

    def save_option_to_server(self, chart_type):
        """ 保存图形的配置到服务器 """
        chart_option = self.get_chart_option()  # 作图配置
        chart_option["chart_category"] = chart_type  # 图表类型(普通图形:normal,季节图形:season)
        title = chart_option["title"]["text"]
        if not title:
            QMessageBox.information(self, "提示", "请填写图形标题!")
            return
        is_private = 1 if self.chart_widget.private_check.checkState() else 0
        json_option = {
            "title": title,
            "variety_en": self.variety_en,
            "decipherment": self.chart_widget.decipherment_edit.text().strip(),
            "is_private": is_private,
            "option": chart_option.copy()
        }
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "sheet/{}/chart/".format(self.sheet_id)
        request = QNetworkRequest(QUrl(url))
        user_token = get_user_token()
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.post(request, json.dumps(json_option).encode("utf-8"))
        reply.finished.connect(self.save_option_reply)

    def save_option_reply(self):
        """ 保存配置返回 """
        reply = self.sender()
        if reply.error():
            QMessageBox.information(self, "失败", "保存配置失败!")
            logger.error("用户保存图形配置失败:{}".format(reply.error()))
        else:
            QMessageBox.information(self, "成功", "保存配置成功!")
        reply.deleteLater()

    def preview_chart_with_option(self):
        """ 在当前窗口预览显示图形 """
        chart_button = self.sender()
        chart_type = getattr(chart_button, "chart_type")
        print("作图类型:\n", chart_type)
        chart_option = self.get_chart_option()  # 作图配置
        chart_source_json = self.get_chart_source_json(chart_type, chart_option, self.source_dataframe)
        print("作图配置:\n", chart_option)
        print("作图源数据:\n", chart_source_json)
        # 将数据和配置传入echarts绘图
        self.chart_widget.show_chart(chart_type, json.dumps(chart_option), json.dumps(chart_source_json))

    def get_chart_option(self):
        """ 获取图形的配置 """
        base_option = self.option_widget.get_base_option()       # 作图基本配置
        more_option = self.more_dispose_popup.get_more_option()  # 作图更多配置
        # 将更多配置添加入基本配置中
        y_axis = base_option["y_axis"]
        # 左轴
        left_more_op = more_option["left_axis"]
        y_axis[0]["name"] = left_more_op["name"]
        if left_more_op["min_value"]:
            y_axis[0]["min"] = left_more_op["min_value"]
        if left_more_op["max_value"]:
            y_axis[0]["max"] = left_more_op["max_value"]
        # 右轴
        if len(y_axis) > 1:
            right_more_op = more_option["right_axis"]
            y_axis[1]["name"] = right_more_op["name"]
            if right_more_op["min_value"]:
                y_axis[1]["min"] = right_more_op["min_value"]
            if right_more_op["max_value"]:
                y_axis[1]["max"] = right_more_op["max_value"]

        return base_option

    def get_chart_source_json(self, chart_type, base_option, source_dataframe):
        """ 处理出绘图的最终数据 """
        values_df = source_dataframe.iloc[2:]
        # 取最大值和最小值
        start_year = base_option["start_year"]
        end_year = base_option["end_year"]
        if start_year > "0":
            start_date = str(start_year) + "-01-01"
            # 切出大于开始日期的数据
            values_df = values_df[values_df["column_0"] >= start_date]
        if end_year > "0":
            # 切出小于结束日期的数据
            end_date = str(end_year) + "-12-31"  # 含结束年份end_year + 1
            values_df = values_df[values_df["column_0"] <= end_date]
        # 数据是否去0处理
        for series_item in base_option["series_data"]:
            column_index = series_item["column_index"]
            contain_zero = series_item["contain_zero"]
            if not contain_zero:  # 数据不含0,去0处理
                values_df = values_df[values_df[column_index] != "0"]
        values_df = values_df.sort_values(by="column_0")  # 最后进行数据从小到大的时间排序
        # table_show_df.reset_index(inplace=True)  # 重置索引,让排序生效(赋予row正确的值。可不操作,转为json后,索引无用处了)
        #
        # 普通图形返回结果数据
        if chart_type == "normal":
            # 处理横轴的格式
            date_length = base_option["x_axis"]["date_length"]
            values_df["column_0"] = values_df["column_0"].apply(lambda x: x[:date_length])
            values_json = values_df.to_dict(orient="record")
        elif chart_type == "season":    # 季节图形将数据分为{year1: values1, year2: values2}型
            values_json = self.get_season_chart_source(values_df.copy())
        else:
            values_json = []
        return values_json

    def get_season_chart_source(self, source_df):
        """ 获取季节图形的作图源数据 """
        target_values = dict()  # 保存最终数据的字典
        target_values["xAxisData"] = self.generate_days_of_year()
        # 获取column_0的最大值和最小值
        min_date = source_df["column_0"].min()
        max_date = source_df["column_0"].max()
        start_year = int(min_date[:4])
        end_year = int(max_date[:4])
        for year in range(start_year, end_year + 1):
            # 获取当年的第一天和最后一天
            current_first = str(year) + "-01-01"
            current_last = str(year) + "-12-31"
            # 从data frame中取本年度的数据并转为列表字典格式
            current_year_df = source_df[(source_df["column_0"] >= current_first) & (source_df["column_0"] <= current_last)]
            current_year_df["column_0"] = current_year_df["column_0"].apply(lambda x: x[5:])
            # target_values[str(year)] = current_year_df.to_dict(orient="record")
            target_values[str(year)] = current_year_df.to_dict(orient="record")
        return target_values

    @staticmethod
    def generate_days_of_year():
        """ 生成一年的每一月每一天 """
        days_list = list()
        start_day = datetime.strptime("2020-01-01", "%Y-%m-%d")
        end_day = datetime.strptime("2020-12-31", "%Y-%m-%d")
        while start_day <= end_day:
            days_list.append(start_day.strftime("%m-%d"))
            start_day += timedelta(days=1)
        return days_list
