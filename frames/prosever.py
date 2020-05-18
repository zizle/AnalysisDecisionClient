# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import json
import chardet
import requests
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QTableWidget, QTextBrowser, \
    QAbstractItemView, QHeaderView, QTableWidgetItem, QPushButton, QFrame
from PyQt5.QtGui import QFont, QBrush,QColor
from widgets import ScrollFoldedBox, LoadedPage, Paginator, PDFContentShower, PDFContentPopup
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QPoint, QMargins
import settings


""" 短信通 """


class TextBrowser(QTextBrowser):
    def wheelEvent(self, event):
        pass


# 短信通控件
class SMSLinkWidget(QWidget):
    def __init__(self, sms_data, *args, **kwargs):
        super(SMSLinkWidget, self).__init__(*args, **kwargs)
        self.sms_id = sms_data['id']
        layout = QVBoxLayout(margin=0, spacing=1)
        option_layout = QHBoxLayout(margin=0)
        date = QDate.fromString(sms_data['date'], 'yyyy-MM-dd')
        time = QTime.fromString(sms_data['time'], 'HH:mm:ss')
        date_time = date.toString('yyyy-MM-dd ') + time.toString('HH:mm') if date != QDate.currentDate() else time.toString('HH:mm')
        option_layout.addWidget(QLabel(date_time, objectName='timeLabel'))
        self.open_button = QPushButton('展开', self, objectName='openCloseBtn')
        self.open_button.clicked.connect(self.resize_text_browser)
        self.open_button.setCursor(Qt.PointingHandCursor)
        option_layout.addWidget(self.open_button, alignment=Qt.AlignRight)
        layout.addLayout(option_layout)
        self.text_browser = TextBrowser(objectName='textBrowser')
        self.text_browser.setText(sms_data['content'])
        self.text_browser.setFixedHeight(27)
        font = QFont()
        font.setPointSize(13)
        self.text_browser.setFont(font)
        self.text_browser.verticalScrollBar().hide()
        layout.addWidget(self.text_browser)
        self.setLayout(layout)
        self.setStyleSheet("""
        #timeLabel{
            font-size:12px;
            color: rgb(50,70,100);
            font-weight: bold;
        }
        #textBrowser{
            margin:0 0 2px 25px;
            border:1px solid rgb(210,210,210);
            color: rgb(0,0,0);
            border-radius: 5px;
            background-color:rgb(225,225,225)
        }
        #openCloseBtn{
            border:none;
            color:rgb(25,75,150)
        }
        """)

    def resize_text_browser(self):
        # print('改变text_browser大小')
        # print(self.text_browser.height(),self.text_browser.document().size().height())
        if self.open_button.text() == "展开":
            self.text_browser.setFixedHeight(self.text_browser.document().size().height() + 5)
            self.open_button.setText("合上")
        else:
            self.text_browser.setFixedHeight(27)
            self.open_button.setText("展开")

    def is_show_open_button(self):
        # print(self.text_browser.height(), self.text_browser.document().size().height())
        if self.text_browser.height() >= self.text_browser.document().size().height():
            self.open_button.hide()


# 短信通主页
class SMSLinkPage(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(SMSLinkPage, self).__init__(*args, **kwargs)
        self.setObjectName("scrollView")
        self.container = QWidget()
        layout = QVBoxLayout()
        self.container.setLayout(layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.read_more_button = QPushButton("<<< 加载更多 >>>", objectName='moreSms', parent=self.container,
                                            clicked=self.read_more_sms, cursor=Qt.PointingHandCursor)
        self.current_page = 1
        self.total_page = 1
        self.currentScrollValue = 0  # 记录当前滚动条的滚动位置，用于填充数据后再次移动到该位置。
        # 设置滚动条样式
        self.setStyleSheet("""
        QScrollArea{
            border: none;
        }
        #moreSms{
            max-width: 200px;
            min-width:200px;
            min-height:60px;
            border:none;
            color:rgb(100, 130, 180);
        }
        """)

    # 请求数据
    def getSMSContents(self, insert_index=0):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'advise/shortmessage/?page='+str(self.current_page))
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError('获取数据失败.')
        except Exception:
            return
        else:
            # 设置当前页和总页数
            self.total_page = response['total_page']
            content = response['records']
            for sms_item in content:
                sms_widget = SMSLinkWidget(sms_item)
                self.container.layout().insertWidget(insert_index, sms_widget)
                # print(sms_widget.text_browser.height())
                # print(sms_widget.text_browser.document().size())
                insert_index += 1
            if self.current_page == 1:  # 加载更多的按钮
                self.container.layout().addWidget(self.read_more_button, alignment=Qt.AlignHCenter)
            if self.current_page < self.total_page:
                self.current_page += 1
                self.read_more_button.setText("<<< 加载更多 >>>")
                self.read_more_button.setEnabled(True)
            else:
                self.read_more_button.setText("- 已经到底了 -")
                self.read_more_button.setEnabled(False)
            self.verticalScrollBar().setValue(self.currentScrollValue)  # 设置滚动条位置

    # 加载更多数据
    def read_more_sms(self):
        self.currentScrollValue = self.verticalScrollBar().value()  # 记录当前的滚动条位置
        count = self.container.layout().count()   # 获取当前的数量
        self.getSMSContents(insert_index=count - 1)


""" 市场分析 """


# 市场分析显示表格
class MarketAnalysisTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(MarketAnalysisTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.cellClicked.connect(self.mouseClickedCell)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setFrameShape(QFrame.NoFrame)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.horizontalHeader().setStyleSheet("""
        QHeaderView::section,
        QTableCornerButton::section {
            min-height: 25px;
            padding: 1px;border: none;
            border-right: 1px solid rgb(201,202,202);
            border-bottom: 1px solid rgb(201,202,202);
            background-color:rgb(243,245,248);
            font-weight: bold;
            font-size: 13px;
            min-width:26px;
        }""")

        self.setStyleSheet("""
        QTableWidget{
            font-size: 14px;
            alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
            background-color: rgb(240,240, 240)
        }
        QTableWidget::item{
            border-bottom: 1px solid rgb(201,202,202);
            border-right: 1px solid rgb(201,202,202);
        }
        QTableWidget::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 3:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseClickedCell(self, row, col):
        if col != 3:
            return
        item = self.item(row, col)
        title = self.item(row, 2).text()
        file_addr = settings.STATIC_PREFIX + item.file_url
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题', '']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem('阅读')
            item3.setForeground(QBrush(QColor(50, 50, 220)))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.file_url = row_item['file_url']
            self.setItem(row, 3, item3)


# 市场分析主页
class MarketAnalysisPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(MarketAnalysisPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 5))
        layout.setSpacing(2)
        self.table = MarketAnalysisTable()
        layout.addWidget(self.table)

        # 无数据的显示
        self.no_data_label = QLabel('暂无市场分析数据...', styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)
        # 页码控制布局
        self.paginator = Paginator()
        self.paginator.setMargins(0, 10, 3, 0)
        self.paginator.clicked.connect(self.getCurrentMarketContents)
        layout.addWidget(self.paginator, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    # 请求数据
    def getCurrentMarketContents(self):
        current_page = self.paginator.current_page
        try:
            url = settings.SERVER_ADDR + 'advise/marketanalysis/?page='+str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            if response['records']:
                self.paginator.setTotalPages(response['total_page'])
                self.table.showRowContents(response['records'])
                self.table.show()
                self.no_data_label.hide()
                self.paginator.show()
            else:
                self.no_data_label.show()
                self.table.hide()
                self.paginator.show()


""" 专题研究 """


# 专题研究显示表格
class TopicSearchTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(TopicSearchTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setShowGrid(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.cellClicked.connect(self.mouseClickedCell)
        self.horizontalHeader().setStyleSheet("""
        QHeaderView::section,
        QTableCornerButton::section {
            min-height: 25px;
            padding: 1px;border: none;
            border-right: 1px solid rgb(201,202,202);
            border-bottom: 1px solid rgb(201,202,202);
            background-color:rgb(243,245,248);
            font-weight: bold;
            font-size: 13px;
            min-width:26px;
        }""")

        self.setStyleSheet("""
        QTableWidget{
            font-size: 14px;
            alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
            background-color: rgb(240,240, 240)
        }
        QTableWidget::item{
            border-bottom: 1px solid rgb(201,202,202);
            border-right: 1px solid rgb(201,202,202);
        }
        QTableWidget::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 3:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseClickedCell(self, row, col):
        if col != 3:
            return
        item = self.item(row, col)
        title = self.item(row, 2).text()
        file_addr = settings.STATIC_PREFIX + item.file_url
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题', '']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem('阅读')
            item3.setForeground(QBrush(QColor(50, 50, 220)))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.file_url = row_item['file_url']
            self.setItem(row, 3, item3)


# 专题研究主页
class TopicSearchPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(TopicSearchPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(QMargins(0,0,0,5))
        self.table = TopicSearchTable()
        layout.addWidget(self.table)
        # 无数据的显示
        self.no_data_label = QLabel('暂无专题研究数据...', styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)

        # 页码控制布局
        self.paginator = Paginator()
        self.paginator.setMargins(0, 10, 3, 0)
        self.paginator.clicked.connect(self.getCurrentTopicContents)
        layout.addWidget(self.paginator, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    # 请求数据
    def getCurrentTopicContents(self):
        current_page = self.paginator.current_page
        try:
            url = settings.SERVER_ADDR + 'advise/topicsearch/?page='+str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            if response['records']:
                self.paginator.setTotalPages(response['total_page'])
                self.table.showRowContents(response['records'])
                self.table.show()
                self.no_data_label.hide()
                self.paginator.show()
            else:
                self.no_data_label.show()
                self.table.hide()
                self.paginator.hide()


""" 调研报告相关 """


# 调研报告显示表格
class SearchReportTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(SearchReportTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.cellClicked.connect(self.mouseClickedCell)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.setStyleSheet("""
        font-size: 14px;
        selection-color: red;
        alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
        """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 3:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseClickedCell(self, row, col):
        if col != 3:
            return
        item = self.item(row, col)
        title = self.item(row, 2).text()
        file_addr = settings.STATIC_PREFIX + item.file_url
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题', '']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem('阅读')
            item3.setForeground(QBrush(QColor(50, 50, 220)))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.file_url = row_item['file_url']
            self.setItem(row, 3, item3)


# 调研报告主页
class SearchReportPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(SearchReportPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 5))
        layout.setSpacing(5)

        self.table = TopicSearchTable()
        layout.addWidget(self.table)
        # 无数据的显示
        self.no_data_label = QLabel('暂无调研报告数据...', styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)

        # 页码控制布局
        self.paginator = Paginator()
        self.paginator.setMargins(0, 10, 3, 0)
        self.paginator.clicked.connect(self.getCurrentReportContents)
        layout.addWidget(self.paginator, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    # 请求数据
    def getCurrentReportContents(self):
        current_page = self.paginator.current_page
        try:
            url = settings.SERVER_ADDR + 'advise/searchreport/?page='+str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            if response['records']:
                self.paginator.setTotalPages(response['total_page'])
                self.table.showRowContents(response['records'])
                self.table.show()
                self.paginator.show()
                self.no_data_label.hide()
            else:
                self.no_data_label.show()
                self.table.hide()
                self.paginator.hide()


""" 策略服务-投资方案相关 """


# 投资方案显示表格
class InvestPlanTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(InvestPlanTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setShowGrid(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.cellClicked.connect(self.mouseClickedCell)
        self.horizontalHeader().setStyleSheet("""
        QHeaderView::section,
        QTableCornerButton::section {
            min-height: 25px;
            padding: 1px;border: none;
            border-right: 1px solid rgb(201,202,202);
            border-bottom: 1px solid rgb(201,202,202);
            background-color:rgb(243,245,248);
            font-weight: bold;
            font-size: 13px;
            min-width:26px;
        }""")

        self.setStyleSheet("""
        QTableWidget{
            font-size: 14px;
            alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
            background-color: rgb(240,240, 240)
        }
        QTableWidget::item{
            border-bottom: 1px solid rgb(201,202,202);
            border-right: 1px solid rgb(201,202,202);
        }
        QTableWidget::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 3:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseClickedCell(self, row, col):
        if col != 3:
            return
        item = self.item(row, col)
        title = self.item(row, 2).text()
        file_addr = settings.STATIC_PREFIX + item.file_url
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题', '']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem('阅读')
            item3.setForeground(QBrush(QColor(50, 50, 220)))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.file_url = row_item['file_url']
            self.setItem(row, 3, item3)


# 投资方案主页
class InvestPlanPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(InvestPlanPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 5))
        layout.setSpacing(2)
        self.table = InvestPlanTable()
        layout.addWidget(self.table)
        # 无数据的显示
        self.no_data_label = QLabel('暂无投资方案数据...', styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)

        # 页码控制布局
        self.paginator = Paginator()
        self.paginator.setMargins(0, 10, 3, 0)
        self.paginator.clicked.connect(self.getCurrentPlanContents)
        layout.addWidget(self.paginator, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    # 请求数据
    def getCurrentPlanContents(self):
        current_page = self.paginator.current_page
        try:
            url = settings.SERVER_ADDR + 'strategy/investmentplan/?page='+str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            if response['records']:
                self.paginator.setTotalPages(response['total_page'])
                self.table.showRowContents(response['records'])
                self.table.show()
                self.no_data_label.hide()
                self.paginator.show()
            else:
                self.no_data_label.show()
                self.paginator.hide()
                self.table.hide()


""" 策略服务-套保方案相关 """


# 套保方案显示表格
class HedgePlanTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(HedgePlanTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)  # 开启交替行颜色
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选中时为一行
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 只能选中一行
        self.cellClicked.connect(self.mouseClickedCell)
        self.setStyleSheet("""
                font-size: 14px;
                selection-color: red;
                alternate-background-color: rgb(245, 250, 248);  /* 设置交替行颜色 */
                """)

    def mouseMoveEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        if index.column() == 3:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseClickedCell(self, row, col):
        if col != 3:
            return
        item = self.item(row, col)
        title = self.item(row, 2).text()
        file_addr = settings.STATIC_PREFIX + item.file_url
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题', '']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem('阅读')
            item3.setForeground(QBrush(QColor(50, 50, 220)))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.file_url = row_item['file_url']
            self.setItem(row, 3, item3)


# 套保方案主页
class HedgePlanPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(HedgePlanPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 5))
        layout.setSpacing(5)

        self.table = InvestPlanTable()
        layout.addWidget(self.table)

        # 无数据的显示
        self.no_data_label = QLabel('暂无套保方案数据...', styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)

        # 页码控制布局
        self.paginator = Paginator()
        self.paginator.setMargins(0, 10, 3, 0)
        self.paginator.clicked.connect(self.getCurrentPlanContents)
        layout.addWidget(self.paginator, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    # 请求数据
    def getCurrentPlanContents(self):
        current_page = self.paginator.current_page
        try:
            url = settings.SERVER_ADDR + 'strategy/hedgeplan/?page='+str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            if response['records']:
                self.paginator.setTotalPages(response['total_page'])
                self.table.showRowContents(response['records'])
                self.table.show()
                self.paginator.show()
                self.no_data_label.hide()
            else:
                self.no_data_label.show()
                self.table.hide()
                self.paginator.hide()


# 产品服务主页
class InfoServicePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(InfoServicePage, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        self.variety_folded = ScrollFoldedBox(parent=self)
        self.variety_folded.left_mouse_clicked.connect(self.enter_service)
        layout.addWidget(self.variety_folded, alignment=Qt.AlignLeft)
        self.frame = LoadedPage(parent=self)
        self.frame.remove_borders()
        layout.addWidget(self.frame)
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
        """)

    # 获取所有品种组和品种
    def addServiceContents(self):
        contents = [
            {
                'name': u'咨询服务',
                'subs': [
                    {'id': 1, 'name': u'短信通'},
                    {'id': 2, 'name': u'市场分析'},
                    {'id': 3, 'name': u'专题研究'},
                    {'id': 4, 'name': u'调研报告'},
                    {'id': 5, 'name': u'市场路演'},
                ]
            },
            {
                'name': u'顾问服务',
                'subs': [
                    {'id': 6, 'name': u'人才培养'},
                    {'id': 7, 'name': u'部门组建'},
                    {'id': 8, 'name': u'制度考核'},
                ]
            },
            {
                'name': u'策略服务',
                'subs': [
                    {'id': 9, 'name': u'交易策略'},
                    {'id': 10, 'name': u'投资方案'},
                    {'id': 11, 'name': u'套保方案'},
                ]
            },
            {
                'name': u'培训服务',
                'subs': [
                    {'id': 12, 'name': u'品种介绍'},
                    {'id': 13, 'name': u'基本分析'},
                    {'id': 14, 'name': u'技术分析'},
                    {'id': 15, 'name': u'制度规则'},
                    {'id': 16, 'name': u'交易管理'},
                    {'id': 17, 'name': u'经验分享'},
                ]
            },
        ]
        for group_item in contents:
            head = self.variety_folded.addHead(group_item['name'])
            body = self.variety_folded.addBody(head=head)
            for sub_item in group_item['subs']:
                body.addButton(id=sub_item['id'], name=sub_item['name'])
        self.variety_folded.container.layout().addStretch()

    def resizeEvent(self, event):
        # 设置折叠菜单的大小
        folded_width = self.parent().width() * 0.23
        self.variety_folded.setFixedWidth(folded_width)
        self.variety_folded.setBodyHorizationItemCount()

    # 点击服务，显示页面
    def enter_service(self, sid, text):
        if sid == 1:  # 短信通
            page = SMSLinkPage(parent=self.frame)
            page.getSMSContents()
        elif sid == 2:  # 市场分析
            page = MarketAnalysisPage(parent=self.frame)
            page.getCurrentMarketContents()
        elif sid == 3:  # 专题研究
            page = TopicSearchPage(parent=self.frame)
            page.getCurrentTopicContents()
        elif sid == 4:  # 调研报告
            page = SearchReportPage(parent=self.frame)
            page.getCurrentReportContents()
        elif sid == 6:  # 顾问服务-人才培养
            page = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/persontrain/人才培养.pdf', parent=self.frame)
        elif sid == 7:  # 顾问服务-部门组建
            page = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/deptbuild/部门组建.pdf', parent=self.frame)
        elif sid == 8:  # 顾问服务-制度考核
            page = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/rulexamine/制度考核.pdf', parent=self.frame)
        elif sid == 10:  # 策略服务-投资方案
            page = InvestPlanPage(parent=self.frame)
            page.getCurrentPlanContents()
        elif sid == 11:  # 策略服务-套保方案
            page = HedgePlanPage(parent=self.frame)
            page.getCurrentPlanContents()
        elif sid == 12:  # 培训服务-品种介绍
            page = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/varietyintro/品种介绍.pdf', parent=self.frame)
        else:
            page = QLabel('当前模块正在加紧开放...',
                          styleSheet='color:rgb(50,180,100); font-size:15px;font-weight:bold', alignment=Qt.AlignCenter)
        self.frame.clear()
        self.frame.addWidget(page)
