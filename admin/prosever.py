# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-19
# ------------------------
import re
import json
import pickle
import requests
from urllib3 import encode_multipart_formdata
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, \
    QTableWidget, QPushButton, QAbstractItemView, QHeaderView, QTableWidgetItem, QGridLayout, QMessageBox, QDialog, QDateEdit, QTimeEdit, QMenu
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QPoint, QMargins, QTime
import settings
from widgets import LoadedPage, PDFContentPopup, Paginator, PDFContentShower, FilePathLineEdit


""" 短信通相关 """


# 创建短信通弹窗
class CreateNewSMSLink(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewSMSLink, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout()
        # 时间布局
        date_time_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        date_time_layout.addWidget(QLabel('日期:'))
        date_time_layout.addWidget(self.date_edit)
        date_time_layout.addWidget(QLabel('时间:'))
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat('HH:mm:ss')
        date_time_layout.addWidget(self.time_edit)
        date_time_layout.addStretch()
        layout.addLayout(date_time_layout)
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        layout.addWidget(QPushButton('确定', clicked=self.commit_sms), alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        self.setWindowTitle('新建短信通')

    # 确定增加
    def commit_sms(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self,'错误', '请输入内容。')
            return
        # 提交
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'advise/shortmessage/',
                headers={'Content-Type': 'application/json;charset=utf8'},
                data=json.dumps({
                    'utoken':settings.app_dawn.value('AUTHORIZATION'),
                    'custom_time': self.date_edit.text() + ' ' + self.time_edit.text(),
                    'content': text
                })
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self,'错误', str(e))
        else:
            QMessageBox.information(self,'成功', "新增成功")
            self.close()


# 维护表格
class SMSTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(SMSTable, self).__init__(*args)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号','时间','内容']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['custom_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['content'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)


# 短信通维护主页
class MessageServiceMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(MessageServiceMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        combo_message_layout = QHBoxLayout()
        # 页码控制器
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getCurrentSMS)
        combo_message_layout.addWidget(self.paginator)
        combo_message_layout.addStretch()
        combo_message_layout.addWidget(QPushButton('新增',parent=self, clicked=self.create_new_sms), alignment=Qt.AlignRight)
        layout.addLayout(combo_message_layout)
        # 展示短信通的表格
        self.sms_table = SMSTable(self)
        layout.addWidget(self.sms_table)
        # 无数据的显示
        self.no_data_label = QLabel('您还没添加短讯通数据...', parent=self, styleSheet='color:rgb(200,100,50)', alignment=Qt.AlignCenter)
        self.no_data_label.hide()
        layout.addWidget(self.no_data_label)
        self.setLayout(layout)

    # 获取当前短信通信息
    def getCurrentSMS(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/shortmessage/?page=' + str(current_page)
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            if response['records']:
                self.sms_table.showRowContents(response['records'])
                self.paginator.setTotalPages(response['total_page'])
                self.sms_table.show()
                self.no_data_label.hide()
            else:
                self.no_data_label.show()
                self.sms_table.hide()

    # 新增一条短信通
    def create_new_sms(self):
        popup = CreateNewSMSLink(parent=self)
        if not popup.exec_():
            self.getCurrentSMS()


"""市场分析"""


# 上传市场分析文件
class CreateNewMarketAnalysisPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewMarketAnalysisPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:',self), 0, 0)
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText('市场分析标题')
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel('文件:', self), 1, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 1, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 2, 0, 1, 2)
        self.setFixedSize(300, 150)
        self.setWindowTitle('新增文件')
        self.setLayout(layout)

    # 上传市场分析
    def commit_upload(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入名称!')
            return
        # 读取文件
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 增加其他字段
        data_file['title'] = name
        # 文件内容字段
        data_file["market_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'advise/marketanalysis/',
                headers={
                    'Content-Type': encode_data[1]
                },
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', '失败:{}'.format(e))
        else:
            QMessageBox.information(self, '成功', '添加数据成功.')
            self.close()


class MarketAnalysisMaintainTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(MarketAnalysisMaintainTable, self).__init__(*args)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameShape(QFrame.NoFrame)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            view_action = rmenu.addAction("查看")
            view_action.triggered.connect(self.view_file_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def view_file_detail(self):
        row = self.currentRow()
        title = self.item(row, 2).text()
        itemfile = self.item(row, 0).file_url
        file_addr = settings.STATIC_PREFIX + itemfile
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/marketanalysis/' + str(itemid) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 市场分析管理主页
class MarketAnalysisMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(MarketAnalysisMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        message_button_layout = QHBoxLayout()
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getFileContents)
        message_button_layout.addWidget(self.paginator)
        message_button_layout.addStretch()
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_analysis_file), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 显示的表格
        self.table = MarketAnalysisMaintainTable()
        layout.addWidget(self.table)
        self.setLayout(layout)

    # 获取内容
    def getFileContents(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            url = settings.SERVER_ADDR + 'user/' + str(user_id) +'/marketanalysis/?page=' + str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.paginator.setTotalPages(response['total_page'])
            self.table.showRowContents(response['records'])
            self.network_message_label.setText(response['message'])

    # 新增一个文件
    def create_analysis_file(self):
        popup = CreateNewMarketAnalysisPopup(parent=self)
        popup.exec_()


"""专题研究"""


# 上传新专题研究文件
class CreateNewTopicSearchPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewTopicSearchPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:', self), 0, 0)
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText('专题研究的标题')
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel('文件:', self), 1, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 1, 1)
        layout.addWidget(QPushButton('确定', parent=self, clicked=self.commit_upload), 2, 0, 1, 2)
        self.setFixedSize(300, 152)
        self.setWindowTitle('新增文件')
        self.setLayout(layout)

    # 上传专题研究
    def commit_upload(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入名称!')
            return
        # 读取文件
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        data_file['title'] = name
        # 文件内容字段
        data_file["topic_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'advise/topicsearch/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', '上传成功!')
            self.close()


# 显示专题研究表格
class TopicSearchMaintainTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(TopicSearchMaintainTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameShape(QFrame.NoFrame)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            view_action = rmenu.addAction("查看")
            view_action.triggered.connect(self.view_file_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def view_file_detail(self):
        row = self.currentRow()
        title = self.item(row, 2).text()
        itemfile = self.item(row, 0).file_url
        file_addr = settings.STATIC_PREFIX + itemfile
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/topicsearch/' + str(itemid) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 专题研究管理
class TopicSearchMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(TopicSearchMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        message_button_layout = QHBoxLayout()
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getFileContents)
        message_button_layout.addWidget(self.paginator)
        message_button_layout.addStretch()
        self.network_message_label = QLabel(self)
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_topic_file), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 显示的表格
        self.table = TopicSearchMaintainTable()
        layout.addWidget(self.table)
        self.setLayout(layout)

    # 获取内容
    def getFileContents(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            url = settings.SERVER_ADDR + 'user/' + str(user_id) + '/topicsearch/?page=' + str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.paginator.setTotalPages(response['total_page'])
            self.table.showRowContents(response['records'])
            self.network_message_label.setText(response['message'])

    # 上传调研报告文件
    def create_topic_file(self):
        popup = CreateNewTopicSearchPopup(parent=self)
        popup.exec_()


"""调研报告"""


# 新增上传调研报告文件
class CreateNewSearchReportPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewSearchReportPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:', self), 0, 0)
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText('调研标题')
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel('文件:',self), 1, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 1, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 2, 1, 1, 2)
        self.setFixedSize(300, 150)
        self.setWindowTitle('新增调研报告')
        self.setLayout(layout)

    # 上传调研报告
    def commit_upload(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入报告名称!')
            return
        # 读取文件
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        data_file['title'] = name
        # 文件内容字段
        data_file["sreport_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'advise/searchreport/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.close()


# 显示调研报告表格
class SearchReportMaintainTable(QTableWidget):

    def __init__(self, *args, **kwargs):
        super(SearchReportMaintainTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '创建日期', '标题']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            view_action = rmenu.addAction("查看")
            view_action.triggered.connect(self.view_file_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def view_file_detail(self):
        row = self.currentRow()
        title = self.item(row, 2).text()
        itemfile = self.item(row, 0).file_url
        file_addr = settings.STATIC_PREFIX + itemfile
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/searchreport/' + str(itemid) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 调研报告管理页面
class SearchReportMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(SearchReportMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        message_button_layout = QHBoxLayout()
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getFileContents)
        message_button_layout.addWidget(self.paginator)
        message_button_layout.addStretch()
        self.network_message_label = QLabel(self)
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_report_file), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 显示的表格
        self.table = SearchReportMaintainTable(self)
        layout.addWidget(self.table)
        self.setLayout(layout)

    # 获取内容
    def getFileContents(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            url = settings.SERVER_ADDR + 'user/' + str(user_id) + '/searchreport/?page=' + str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.paginator.setTotalPages(response['total_page'])
            self.table.showRowContents(response['records'])
            self.network_message_label.setText(response['message'])

    # 上传调研报告文件
    def create_report_file(self):
        popup = CreateNewSearchReportPopup(parent=self)
        popup.exec_()


"""人才培养"""


# 修改人才培养显示的文件
class ModifyPersonnelTrainPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(ModifyPersonnelTrainPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout()
        layout.addWidget(QLabel('文件:', self), 0, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 0, 1)
        layout.addWidget(QPushButton('确定',parent=self, clicked=self.commit_upload), 1, 1, 1, 2)
        self.setFixedSize(200, 120)
        self.setWindowTitle('修改文件')
        self.setLayout(layout)

    # 修改人才培养显示文件内容
    def commit_upload(self):
        # 读取文件
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 文件内容字段
        data_file["pt_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'consult/persontrain/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.close()


# 人才培养数据管理主页
class PersonnelTrainMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(PersonnelTrainMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        layout.addWidget(QPushButton('修改', parent=self, clicked=self.modify_file), alignment=Qt.AlignRight)
        # 显示服务端pdf文件
        content_show = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/persontrain/人才培养.pdf', parent=self)
        layout.addWidget(content_show)
        self.setLayout(layout)

    # 修改人才培养显示的文件
    def modify_file(self):
        popup = ModifyPersonnelTrainPopup(parent=self)
        popup.exec_()


"""部门组建"""


# 修改部门组建文件
class ModifyDeptBuildPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(ModifyDeptBuildPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('文件:', self), 0, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 0, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 1, 0, 1, 2)
        self.setFixedSize(250, 120)
        self.setWindowTitle('修改文件')
        self.setLayout(layout)

    # 修改部门组建文件内容
    def commit_upload(self):
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 文件内容字段
        data_file["depb_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'consult/deptbuild/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '错误', response['message'])
            self.close()


# 部门组建管理
class DeptBuildMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(DeptBuildMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        layout.addWidget(QPushButton('修改', clicked=self.modify_file), alignment=Qt.AlignRight)
        # 显示服务端pdf文件
        content_show = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/deptbuild/部门组建.pdf', parent=self)
        layout.addWidget(content_show)
        self.setLayout(layout)

    # 修改部门组建显示的文件
    def modify_file(self):
        popup = ModifyDeptBuildPopup(parent=self)
        popup.exec_()


"""制度考核"""


# 制度考核文件修改
class ModifyInstExaminePopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(ModifyInstExaminePopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('文件:', self), 0, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 0, 1)
        layout.addWidget(QPushButton('确定', parent=self, clicked=self.commit_upload), 1, 0, 1, 2)
        self.setFixedSize(250, 120)
        self.setWindowTitle('修改文件')
        self.setLayout(layout)

    # 修改制度考核文件
    def commit_upload(self):
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 文件内容字段
        data_file["rxm_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'consult/rulexamine/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '错误', response['message'])
            self.close()


# 制度考核管理
class InstExamineMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(InstExamineMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        layout.addWidget(QPushButton('修改', parent=self, clicked=self.modify_file), alignment=Qt.AlignRight)
        # 显示服务端pdf文件
        content_show = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/rulexamine/制度考核.pdf', parent=self)
        layout.addWidget(content_show)
        self.setLayout(layout)

    # 修改制度考核显示的文件
    def modify_file(self):
        popup = ModifyInstExaminePopup(parent=self)
        popup.exec_()


"""交易策略"""


"""投资方案"""


# 上传投资方案
class CreateNewInvestPlanPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewInvestPlanPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:', self), 0, 0)
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel('文件:', self), 1, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 1, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 2, 1, 1, 2)
        self.setFixedSize(300, 150)
        self.setWindowTitle('新增方案')
        self.setLayout(layout)

    # 上传方案文件
    def commit_upload(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入方案名称')
            return
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # 文件内容字段
        data_file["invest_file"] = (file_name, file_content)
        # 增加其他字段
        data_file['title'] = name
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'strategy/investmentplan/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.close()


# 显示投资方案表格
class InvestPlanMaintainTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(InvestPlanMaintainTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '日期', '方案标题']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            view_action = rmenu.addAction("查看")
            view_action.triggered.connect(self.view_file_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def view_file_detail(self):
        row = self.currentRow()
        title = self.item(row, 2).text()
        itemfile = self.item(row, 0).file_url
        file_addr = settings.STATIC_PREFIX + itemfile
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/investmentplan/' + str(itemid) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 投资方案管理
class InvestPlanMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(InvestPlanMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        message_button_layout = QHBoxLayout()
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getFileContents)
        message_button_layout.addWidget(self.paginator)
        message_button_layout.addStretch()
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', parent=self, clicked=self.create_topic_file), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 显示的表格
        self.table = InvestPlanMaintainTable()
        layout.addWidget(self.table)
        self.setLayout(layout)

    # 获取内容
    def getFileContents(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            url = settings.SERVER_ADDR + 'user/' + str(user_id) + '/investmentplan/?page='+ str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.paginator.setTotalPages(response['total_page'])
            self.table.showRowContents(response['records'])
            self.network_message_label.setText(response['message'])

    # 上传投资方案文件
    def create_topic_file(self):
        popup = CreateNewInvestPlanPopup(parent=self)
        popup.exec_()


"""套保方案"""


# 上传套保方案
class CreateNewHedgePlanPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewHedgePlanPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('名称:', self), 0, 0)
        self.name_edit = QLineEdit(self)
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel('文件:', self), 1, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 1, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 2, 0, 1, 2)
        self.setFixedSize(300, 150)
        self.setWindowTitle('新增方案')
        self.setLayout(layout)

    # 上传套保方案文件
    def commit_upload(self):
        name = re.sub(r'\s+', '', self.name_edit.text())
        if not name:
            QMessageBox.information(self, '错误', '请输入套保方案名称')
            return
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        data_file['title'] = name
        # 文件内容字段
        data_file["hedge_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'strategy/hedgeplan/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.close()


# 显示套保方案表格
class HedgePlanMaintainTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(HedgePlanMaintainTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setObjectName('showTable')
        self.setStyleSheet("""
        #showTable{
            background-color:rgb(240,240,240);
            alternate-background-color: rgb(245, 250, 248);
        }
        #showTable::item:selected{
            background-color: rgb(215, 215, 215);
        }
        """)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号', '日期', '方案标题']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['create_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['title'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            view_action = rmenu.addAction("查看")
            view_action.triggered.connect(self.view_file_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

        # super(ReportTable, self).mousePressEvent(event)  # 事件不再往外传了

    def view_file_detail(self):
        row = self.currentRow()
        title = self.item(row, 2).text()
        itemfile = self.item(row, 0).file_url
        file_addr = settings.STATIC_PREFIX + itemfile
        popup = PDFContentPopup(title=title, file=file_addr)
        popup.exec_()

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/hedgeplan/' + str(itemid) + '/?utoken=' + settings.app_dawn.value('AUTHORIZATION')
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 套保方案管理
class HedgePlanMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(HedgePlanMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        message_button_layout = QHBoxLayout()
        self.paginator = Paginator()
        self.paginator.clicked.connect(self.getFileContents)
        message_button_layout.addWidget(self.paginator)
        message_button_layout.addStretch()
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_topic_file), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 显示的表格
        self.table = HedgePlanMaintainTable()
        layout.addWidget(self.table)
        self.setLayout(layout)

    # 获取内容
    def getFileContents(self):
        current_page = self.paginator.current_page
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            url = settings.SERVER_ADDR + 'user/'+ str(user_id) + '/hedgeplan/?page=' + str(current_page)
            r = requests.get(url=url)
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.paginator.setTotalPages(response['total_page'])
            self.table.showRowContents(response['records'])
            self.network_message_label.setText(response['message'])

    # 上传套保方案文件
    def create_topic_file(self):
        popup = CreateNewHedgePlanPopup(parent=self)
        popup.exec_()


"""品种介绍"""


# 修改品种介绍文件
class ModifyVarietyIntroPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(ModifyVarietyIntroPopup, self).__init__(*args, **kwargs)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('文件:', self), 0, 0)
        self.file_edit = FilePathLineEdit(self)
        layout.addWidget(self.file_edit, 0, 1)
        layout.addWidget(QPushButton('确定', clicked=self.commit_upload), 1, 1, 1, 2)
        self.setFixedSize(250, 120)
        self.setWindowTitle('修改文件')
        self.setLayout(layout)

    # 修改品种介绍显示文件内容
    def commit_upload(self):
        try:
            file_path = self.file_edit.text()
            file_name = file_path.rsplit('/', 1)[1]
            file = open(file_path, "rb")
            file_content = file.read()
            file.close()
        except Exception as e:
            QMessageBox.information(self, '错误', '打开文件失败,请选择正确的文件路径')
            return
        data_file = dict()
        # # 增加其他字段
        data_file['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 文件内容字段
        data_file["variety_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data_file)
        data_file = encode_data[0]
        # 发起上传请求
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'train/varietyintro/',
                headers={'Content-Type': encode_data[1]},
                data=data_file
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self, '错误', str(e))
        else:
            QMessageBox.information(self, '成功', response['message'])
            self.close()


# 品种介绍管理
class VarietyIntroMaintain(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietyIntroMaintain, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        layout.addWidget(QPushButton('修改', clicked=self.modify_file), alignment=Qt.AlignRight)
        # 显示服务端pdf文件
        content_show = PDFContentShower(file=settings.STATIC_PREFIX + 'pserver/varietyintro/品种介绍.pdf', parent=self)
        layout.addWidget(content_show)
        self.setLayout(layout)

    def modify_file(self):
        popup = ModifyVarietyIntroPopup(parent=self)
        popup.exec_()


# 产品服务管理主页
class ProductServiceAdmin(QWidget):
    def __init__(self, *args, **kwargs):
        super(ProductServiceAdmin, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        # 左侧管理菜单
        self.left_tree = QTreeWidget(parent=self, clicked=self.left_tree_clicked)
        self.left_tree.header().hide()
        layout.addWidget(self.left_tree, alignment=Qt.AlignLeft)
        # 右侧显示窗口
        self.right_frame = LoadedPage()
        self.right_frame.remove_borders()
        layout.addWidget(self.right_frame)
        self.setLayout(layout)

        self.left_tree.setObjectName('leftTree')
        self.setStyleSheet("""
        #leftTree{
            border:none;
            background-color:rgb(240,240,240);
            border-right: 1px solid rgb(180,180,180);
        }
        #leftTree::item{
            height:25px;
        }
        """)

    # 添加管理菜单
    def add_left_tree_menus(self):
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
        # 填充树
        for group_item in contents:
            group = QTreeWidgetItem(self.left_tree)
            group.setText(0, group_item['name'])
            # 添加子节点
            for variety_item in group_item['subs']:
                child = QTreeWidgetItem()
                child.setText(0, variety_item['name'])
                child.sid = variety_item['id']
                group.addChild(child)
        self.left_tree.expandAll()  # 展开所有

    # 点击左侧菜单
    def left_tree_clicked(self):
        item = self.left_tree.currentItem()
        if item.childCount():  # has children open the root
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
            return
        service_id = item.sid
        text = item.text(0)
        if service_id == 1:  # 短信通
            page = MessageServiceMaintain()
            page.getCurrentSMS()
        elif service_id == 2:  # 市场分析
            page = MarketAnalysisMaintain()
            page.getFileContents()
        elif service_id == 3:  # 专题研究
            page = TopicSearchMaintain()
            page.getFileContents()
        elif service_id == 4:  # 调研报告
            page = SearchReportMaintain()
            page.getFileContents()
        elif service_id == 6:  # 人才培养
            page = PersonnelTrainMaintain()
        elif service_id == 7:  # 部门组建
            page = DeptBuildMaintain()
        elif service_id == 8:  # 制度考核
            page = InstExamineMaintain()
        elif service_id == 10:  # 投资方案
            page = InvestPlanMaintain()
            page.getFileContents()
        elif service_id == 11:  # 套保方案
            page = HedgePlanMaintain()
            page.getFileContents()
        elif service_id == 12:  # 培训服务-品种介绍
            page = VarietyIntroMaintain()
        else:
            page = QLabel('【' + text + '】还不能进行数据管理...',
                          styleSheet='color:rgb(50,180,100); font-size:15px;font-weight:bold', alignment=Qt.AlignCenter)
        self.right_frame.clear()
        self.right_frame.addWidget(page)
