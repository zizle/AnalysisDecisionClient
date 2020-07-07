# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import json
import requests
import pandas as pd
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QFrame, QHeaderView, QTableWidgetItem, \
    QLabel, QScrollArea
from PyQt5.QtGui import QBrush, QColor
# from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QMargins, Qt, QPoint
from widgets import ScrollFoldedBox
import settings


# 显示数据的table
class DetailTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(DetailTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QHeaderView.NoEditTriggers)

    def show_detail_data(self, table_headers, table_records):
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(table_records))
        self.setHorizontalHeaderLabels(table_headers)
        for row, row_item in enumerate(table_records):
            for col in range(len(table_headers)):
                data_key = "column_{}".format(col)
                item = QTableWidgetItem(row_item[data_key])
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row, col, item)


# 双击进入查看数据和图表弹窗
class ChartTablePopup(QScrollArea):
    def __init__(self, tid, sql_table, *args, **kwargs):
        super(ChartTablePopup, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.table_id = tid
        self.sql_table = sql_table
        self.resize(980, 650)
        self.sorted_df = None
        self.table_headers = None

        self.container = QWidget(self)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0,0,0,0)

        self.show_table = DetailTable(self)
        layout.addWidget(self.show_table)
        self.container.setLayout(layout)

        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self._get_current_table_data()

    # 请求当前table的源数据
    def _get_current_table_data(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/'
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            settings.logger.error("请求源数据表错误:{}".format(e))
        else:
            table_records = response['records']
            table_headers_dict = table_records.pop(0)  # 表头
            if self.table_headers is not None:
                del self.table_headers
                self.table_headers = None
            del table_headers_dict['id']
            del table_headers_dict['create_time']
            del table_headers_dict['update_time']
            self.table_headers = [header for header in table_headers_dict.values()]
            table_records.pop(0)  # 去掉第3无关紧要(单位等)行
            # sort data
            self.sorted_source_data(table_records)
            # show data
            self.table_show_detail_data()

    # 显示数据到表格中
    def table_show_detail_data(self):
        if self.sorted_df is None or self.table_headers is None:
            return
        dict_data = self.sorted_df.to_dict(orient="records")
        self.show_table.show_detail_data(self.table_headers, dict_data)

    # 根据时间排序数据
    def sorted_source_data(self, table_records):
        source_df = pd.DataFrame(table_records)
        source_df['column_0'] = pd.to_datetime(source_df["column_0"], format='%Y-%m-%d')
        source_df['column_0'] = source_df["column_0"].apply(lambda x: x.strftime('%Y-%m-%d'))
        if self.sorted_df is not None:
            del self.sorted_df
            self.sorted_df = None
        self.sorted_df = source_df.sort_values(by='column_0')
        self.sorted_df.reset_index(drop=True, inplace=True)  # 重置数据索引


# 来源与备注的信息弹窗
class InformationPopup(QLabel):
    def __init__(self, title, text, *args):
        super(InformationPopup, self).__init__(*args)
        self.setWordWrap(True)
        self.setWindowTitle(title)
        self.setText(text)
        self.setWindowFlags(Qt.Dialog)
        self.setFixedSize(200,130)


# 数据表的表格
class DataTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(DataTableWidget, self).__init__(*args)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionBehavior(QHeaderView.SelectRows)
        self.setEditTriggers(QHeaderView.NoEditTriggers)
        self.verticalHeader().hide()
        self.cellClicked.connect(self.cell_clicked)  # 单击显示来源或者备注
        self.cellDoubleClicked.connect(self.double_clicked)  # 双击进入详情
        self.show_information = InformationPopup('', '', self)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() in [4, 5]:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def cell_clicked(self, row, col):
        if col in [4, 5]:
            title = "来源" if col == 4 else "备注"
            text = self.item(row, col).show_text
            self.show_information.setWindowTitle(title)
            self.show_information.setText(text)
            if self.show_information.isHidden():
                self.show_information.show()

    def double_clicked(self, row, col):
        table_id = self.item(row, 0).id
        sql_table = self.item(row, 0).sql_table
        title = self.item(row, 1).text()
        popup = ChartTablePopup(table_id, sql_table, self.parent())
        popup.setWindowTitle(title)
        popup.show()

    def show_tables(self, table_list):
        table_headers = ["序号", "标题", "起始时间", "截止时间", "数据来源", "备注"]
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.setRowCount(len(table_list))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for row, row_item in enumerate(table_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.id = row_item["id"]
            item0.sql_table = row_item["sql_table"]
            item0.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item["title"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item["min_date"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item["max_date"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem("来源")
            item4.show_text = row_item["origin"]
            item4.setForeground(QBrush(QColor(50, 50, 150)))
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem("备注")
            item5.show_text = ""
            item5.setForeground(QBrush(QColor(150, 50, 50)))
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)


# 基本分析主页
class TrendPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(TrendPage, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        self.variety_folded = ScrollFoldedBox()
        self.variety_folded.left_mouse_clicked.connect(self.variety_clicked)
        layout.addWidget(self.variety_folded, alignment=Qt.AlignLeft)
        # 右侧是QTableWidget用于显示数据表信息
        tableinfo_layout = QVBoxLayout(self)
        tableinfo_layout.setContentsMargins(1,1,0,1)
        self.data_table = DataTableWidget(self)
        tableinfo_layout.addWidget(self.data_table)
        layout.addLayout(tableinfo_layout)

        # self.web_charts = QWebEngineView(self)
        #
        # layout.addWidget(self.web_charts)

        self.setLayout(layout)
        # 设置折叠窗的样式
        self.variety_folded.setFoldedStyleSheet("""
        QScrollArea{
            border: none;
        }
        #foldedBox{
            border-right: 1px solid rgb(180, 180, 180);
        }
        #foldedHead{
            background-color: rgb(145,202,182);
            border-bottom: 1px solid rgb(200,200,200);
            border-right: 1px solid rgb(180, 180, 180);
            max-height: 30px;
        }
        #headLabel{
            padding:8px 5px;
            font-weight: bold;
            font-size: 15px;
        }
        #foldedBody{
            background-color: rgb(240, 240, 240);
            border-right: 1px solid rgb(180, 180, 180);
        }
        /*折叠窗内滚动条样式*/
        #foldedBox QScrollBar:vertical{
            width: 5px;
            background: transparent;
        }
        #foldedBox QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 30);
            width: 5px;
            border-radius: 5px;
            border: none;
        }
        #foldedBox QScrollBar::handle:vertical:hover,QScrollBar::handle:horizontal:hover {
            background: rgba(0, 0, 0, 80);
        }
        """)

    def resizeEvent(self, event):
        # 设置折叠窗的大小
        box_width = self.parent().width() * 0.228
        self.variety_folded.setFixedWidth(box_width + 8)
        self.variety_folded.setBodyHorizationItemCount()
        # self.web_charts.setMinimumWidth(self.parent().width() - box_width)  # 设置页面显示的大小
        # self.web_charts.reload()

    # def _get_all_charts(self, variety_id=0):
    #     self.web_charts.load(QUrl(settings.SERVER_ADDR + 'trend/charts/?is_render=1' + '&variety=' + str(variety_id)))

    # 获取所有品种组和品种
    def getGroupVarieties(self):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/?way=group')
            if r.status_code != 200:
                raise ValueError('获取失败!')
            response = json.loads(r.content.decode('utf-8'))
        except Exception:
            pass
        else:
            for group_item in response['variety']:
                head = self.variety_folded.addHead(group_item['name'])
                body = self.variety_folded.addBody(head=head)
                for sub_item in group_item['subs']:
                    body.addButton(sub_item['id'], sub_item['name'])
            self.variety_folded.container.layout().addStretch()

    # 点击了品种,请求当前品种下的所有数据表
    def variety_clicked(self, vid, text):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/{}/trend/table/'.format(vid))
            if r.status_code != 200:
                raise ValueError("获取品种该数据表失败!")
            response = json.loads(r.content.decode('utf8'))
        except Exception as e:
            print(e)
        else:
            print(response)
            self.data_table.show_tables(response["tables"])
        # self._get_all_charts(variety_id=vid)

