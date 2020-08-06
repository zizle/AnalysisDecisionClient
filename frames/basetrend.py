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
    QLabel, QPushButton
from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QMargins, Qt, QPoint, QThread, pyqtSignal
from widgets import ScrollFoldedBox, CircleProgressBar
import settings


# 显示数据的table
class DetailTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(DetailTable, self).__init__(*args)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QHeaderView.NoEditTriggers)

    def show_detail_data(self, table_headers, table_records):
        headers_list = list()
        for col_index in range(len(table_headers)):
            headers_list.append(table_headers["column_{}".format(col_index)])
        table_headers = headers_list
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(table_records))
        self.setHorizontalHeaderLabels(table_headers)
        for row, row_item in enumerate(table_records):
            for col in range(len(table_headers)):
                data_key = "column_{}".format(col)
                item = QTableWidgetItem(row_item[data_key])
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row, col, item)


# 来源与备注的信息弹窗
class InformationPopup(QLabel):
    def __init__(self, title, text, *args):
        super(InformationPopup, self).__init__(*args)
        self.setWordWrap(True)
        self.setWindowTitle(title)
        self.setText(text)
        self.setWindowFlags(Qt.Dialog)
        self.resize(200, 130)
        self.setAlignment(Qt.AlignCenter)


# 请求table源数据的线程
class GetTableSourceThread(QThread):
    source_data_signal = pyqtSignal(int, str, list)

    def __init__(self, table_id,title,*args, **kwargs):
        super(GetTableSourceThread, self).__init__(*args, **kwargs)
        self.table_id = table_id
        self.title = title

    def run(self):
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
            self.source_data_signal.emit(self.table_id, self.title, response['records'])


# 显示图形的WebView
class ChartsWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super(ChartsWebEngineView, self).__init__(*args, **kwargs)


# 显示图形和数据的弹窗
class ChartOfTableWidget(QWidget):
    def __init__(self, table_id, source_data, *args, **kwargs):
        super(ChartOfTableWidget, self).__init__(*args, **kwargs)
        self.sorted_df = None
        self.table_headers_dict = None
        self.setWindowFlags(Qt.Dialog)
        self.table_id = table_id
        self.source_data = source_data
        self.resize(960, 650)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.detail_table = DetailTable(self)
        self.detail_table.setMaximumHeight(220)
        # 显示图形的WebView
        self.charts_show = ChartsWebEngineView(self)
        layout.addWidget(self.charts_show)
        layout.addWidget(self.detail_table)
        self.setLayout(layout)
        self._sort_and_show_table_data()
        self.charts_show.load(QUrl(settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/charts/'))

    # 对数据进行时间列column_0的排序
    def _sort_and_show_table_data(self):
        table_headers_dict = self.source_data.pop(0)  # 表头
        free_row = self.source_data.pop(0)  # 第3行
        del table_headers_dict['id']
        del table_headers_dict['create_time']
        del table_headers_dict['update_time']
        self.table_headers_dict = table_headers_dict
        source_df = pd.DataFrame(self.source_data)
        source_df['column_0'] = pd.to_datetime(source_df["column_0"], format='%Y-%m-%d')
        source_df['column_0'] = source_df["column_0"].apply(lambda x: x.strftime('%Y-%m-%d'))
        if self.sorted_df is not None:
            del self.sorted_df
            self.sorted_df = None
        self.sorted_df = source_df.sort_values(by='column_0')
        self.sorted_df.reset_index(drop=True, inplace=True)  # 重置数据索引
        table_records = self.sorted_df.to_dict(orient='records')
        table_records.insert(0, free_row)
        self.detail_table.show_detail_data(self.table_headers_dict, table_records)
        del self.source_data
        self.source_data = None


# 数据表的表格
class DataTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(DataTableWidget, self).__init__(*args)
        self.is_loading_data = False
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionBehavior(QHeaderView.SelectRows)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setEditTriggers(QHeaderView.NoEditTriggers)
        self.verticalHeader().hide()
        self.cellClicked.connect(self.cell_clicked)  # 单击显示来源或者备注
        self.cellDoubleClicked.connect(self.view_chart_of_table)  # 双击进入图表详情
        self.show_information = InformationPopup('', '', self)
        self.loading_process = CircleProgressBar(self)
        self.loading_process.hide()
        self.setObjectName('dataTable')
        self.setStyleSheet("""
        #dataTable{
            background-color:rgb(240,240,240);
            font-size: 13px;
            selection-color: rgb(180,60,60);
            selection-background-color: rgb(220,220,220);
            alternate-background-color: rgb(245, 250, 248);
        }
        """)
        # 获取数据的线程
        self.get_source_thread = None

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

    def show_tables(self, table_list):
        table_headers = ["序号", "标题", "起始时间", "截止时间", "数据来源", "备注", ""]

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
            item5.show_text = row_item["note"]
            item5.setForeground(QBrush(QColor(150, 50, 50)))
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)
            chart_count = row_item["charts_count"]
            btn = QPushButton(str(chart_count), self) if chart_count else QPushButton(self)
            btn.setStyleSheet("border:none;color:rgb(50,160,100)")
            btn.resize(50, 50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(QIcon('media/nor_chart.png'))
            btn.row = row
            btn.clicked.connect(self.view_chart_of_table)
            self.setCellWidget(row, 6, btn)

    def show_loading_bar(self):
        if self.is_loading_data:
            self.loading_process.show()
        else:
            self.loading_process.hide()

    # 查看当前数据表下的图形
    def view_chart_of_table(self, row=None, col=None):
        self.loading_process.move(self.frameGeometry().width() / 2 - 35, self.frameGeometry().height() / 2 - 35)
        self.loading_process.show()
        if not row:
            row = self.sender().row
        table_id = self.item(row, 0).id
        title = self.item(row, 1).text()
        # 线程获取数据
        if self.get_source_thread is not None:
            del self.get_source_thread
        self.get_source_thread = GetTableSourceThread(table_id=table_id, title=title)
        self.get_source_thread.source_data_signal.connect(self.table_source_back)
        self.get_source_thread.finished.connect(self.get_source_thread.deleteLater)
        self.get_source_thread.start()

    def table_source_back(self, table_id, title, table_source_data):
        popup = ChartOfTableWidget(table_id, table_source_data, self)
        popup.setWindowTitle(title)
        self.loading_process.hide()
        popup.show()


# 基本分析主页
class TrendPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(TrendPage, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        self.variety_folded = ScrollFoldedBox()
        self.variety_folded.left_mouse_clicked.connect(self.variety_clicked)
        layout.addWidget(self.variety_folded)
        # 右侧是QTableWidget用于显示数据表信息

        # tableinfo_layout.addWidget(self.data_table)
        # layout.addLayout(tableinfo_layout)
        # 右侧是webView
        r_layout = QVBoxLayout(self)
        self.table_lib_btn = QPushButton("数据库", self, objectName='libBtn')
        self.table_lib_btn.setToolTip("点击查看当前品种数据表")
        self.table_lib_btn.setCursor(Qt.PointingHandCursor)
        self.table_lib_btn.hide()
        self.table_lib_btn.clicked.connect(self.reverse_charts_and_table)
        r_layout.addWidget(self.table_lib_btn, alignment=Qt.AlignLeft)
        self.charts_loader = QWebEngineView(self)
        r_layout.addWidget(self.charts_loader)

        self.data_table = DataTableWidget(self)
        r_layout.addWidget(self.data_table)
        self.data_table.hide()

        layout.addLayout(r_layout)

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
        self.setStyleSheet("""
        #libBtn{border:none;color:rgb(50,120,180);padding:3px 8px;font-size:13px}
        #libBtn:hover{color:rgb(50,150,230);font-weight:bold}
        """)
        self.charts_loader.load(QUrl(settings.SERVER_ADDR + 'trend/charts/'))

    def resizeEvent(self, event):
        # 设置折叠窗的大小
        box_width = self.parent().width() * 0.228
        self.variety_folded.setFixedWidth(box_width + 8)
        self.variety_folded.setBodyHorizationItemCount()
        self.charts_loader.setFixedWidth(self.parent().width() - box_width - 8)

    # 获取所有品种组和品种
    def getGroupVarieties(self):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/?way=group')
            if r.status_code != 200:
                raise ValueError('获取失败!')
            response = json.loads(r.content.decode('utf-8'))
        except Exception as e:
            settings.logger.error("【基本分析】模块获取左侧品种菜单失败:{}".format(e))
        else:
            for group_item in response['variety']:
                head = self.variety_folded.addHead(group_item['name'])
                body = self.variety_folded.addBody(head=head)
                for sub_item in group_item['subs']:
                    body.addButton(sub_item['id'], sub_item['name'])
            self.variety_folded.container.layout().addStretch()

    # 点击了品种，显示当前品种下的品种页显示的图形
    def variety_clicked(self, vid, text):
        self.charts_loader.load(QUrl(settings.SERVER_ADDR + 'trend/variety-charts/'+str(vid)+'/'))
        self.get_current_variety_table(vid, text)

    # 点击了品种,请求当前品种下的所有数据表
    def get_current_variety_table(self, vid, text):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/{}/trend/table/'.format(vid))
            if r.status_code != 200:
                raise ValueError("获取品种该数据表失败!")
            response = json.loads(r.content.decode('utf8'))
        except Exception as e:
            settings.logger.error("【基本分析】模块获取品种下的数据表失败:{}".format(e))
        else:
            self.data_table.show_tables(response["tables"])
            self.table_lib_btn.show()

    # 切换图形与表格的显示
    def reverse_charts_and_table(self):
        if self.data_table.isHidden():
            self.charts_loader.hide()
            self.data_table.show()
            self.table_lib_btn.setText("图形库")
            self.table_lib_btn.setToolTip("点击查看当前品种图形")
        else:
            self.data_table.hide()
            self.charts_loader.show()
            self.table_lib_btn.setText("数据库")
            self.table_lib_btn.setToolTip("点击查看当前品种数据表")
