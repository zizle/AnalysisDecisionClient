# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-19
# ------------------------
import os
import re
import json
import requests
import pickle
from urllib3 import encode_multipart_formdata
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QListWidget, QLabel, QDialog, QGridLayout, QTreeWidget, QTreeWidgetItem, \
    QPushButton, QHeaderView, QTableWidget, QAbstractItemView, QTableWidgetItem, QLineEdit, QMenu, QMessageBox, QComboBox, QDateEdit, QFileDialog, \
    QProgressBar, QTimeEdit, QTextEdit
from PyQt5.QtGui import QCursor, QRegExpValidator
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QMargins, QDate, QRegExp, QTime
from widgets import LoadedPage, FilePathLineEdit, PDFContentPopup
import settings

""" 新闻公告 """


# 新增新闻
class CreateNewsPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewsPopup, self).__init__(*args, **kwargs)
        self.setFixedSize(300, 150)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("新闻公告")
        layout = QGridLayout()
        layout.setParent(self)
        layout.addWidget(QLabel("标题:", self), 0, 0)
        self.bulletin_title = QLineEdit(self)
        layout.addWidget(self.bulletin_title, 0, 1)
        layout.addWidget(QLabel("文件:", self), 1, 0)
        self.file_path_edit = FilePathLineEdit()
        self.file_path_edit.setParent(self)
        layout.addWidget(self.file_path_edit, 1, 1)
        self.commit_button = QPushButton("提交", self)
        self.commit_button.clicked.connect(self.upload_news)
        layout.addWidget(self.commit_button, 2, 0, 1, 2)
        self.setLayout(layout)

    # 公告上传的请求
    def upload_news(self):
        self.commit_button.setEnabled(False)
        title = re.sub(r'\s+', '', self.bulletin_title.text())
        if not title:
            QMessageBox.information(self, "错误", "标题不能为空!")
            return
        data = dict()
        data['bulletin_title'] = title  # 标题

        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.information(self, "错误", "请选择文件!")
            return
        file_name = file_path.rsplit('/', 1)[1]
        file = open(file_path, "rb")  # 获取文件
        file_content = file.read()
        file.close()
        data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        # 文件内容字段
        data["bulletin_file"] = (file_name, file_content)
        encode_data = encode_multipart_formdata(data)
        try:
            # 发起上传请求
            r = requests.post(
                url=settings.SERVER_ADDR + 'bulletin/',
                headers={
                    'Content-Type': encode_data[1]
                },
                data=encode_data[0]
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, '错误', "上传数据错误!")
        else:
            QMessageBox.information(self, '错误', "上传成功!")
        finally:
            self.commit_button.setEnabled(True)
            self.close()


# 新闻公告显示的表格
class NewsBulletinTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(NewsBulletinTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    # 显示数据
    def showRowContens(self, news_list):
        self.clear()
        table_headers = ["序号", "标题"]
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(news_list):
            self.insertRow(row)
            item0 = QTableWidgetItem(str(row + 1))
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            item0.setTextAlignment(Qt.AlignCenter)
            self.setItem(row,0, item0)
            item1 = QTableWidgetItem(row_item['title'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)


# 新闻公告页面
class NewsBulletinPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(NewsBulletinPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)
        # 信息展示与新增按钮
        message_button_layout = QHBoxLayout()
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addWidget(QPushButton('新增', parent=self, clicked=self.create_news), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 当前数据显示表格
        self.news_table = NewsBulletinTable()
        self.news_table.network_result.connect(self.network_message_label.setText)
        layout.addWidget(self.news_table)
        self.setLayout(layout)
        self.current_page = 1
        self.total_page = 1
        self.page_size = 50

    # 获取所有的新闻公告内容
    def getNewsBulletins(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'bulletin/?page={}&page_size={}'.format(self.current_page, self.page_size),
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.news_table.showRowContens(response['bulletins'])
            self.network_message_label.setText(response['message'])

    # 新增新闻
    def create_news(self):
        popup = CreateNewsPopup(parent=self)
        popup.exec_()


""" 常规报告 """


# 新增常规报告
class CreateReportPopup(QDialog):
    def __init__(self, variety_info, *args, **kwargs):
        super(CreateReportPopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("新建报告")
        self.variety_info = variety_info
        # 总布局-左右
        layout = QHBoxLayout()
        # 左侧上下布局
        llayout = QVBoxLayout()
        # 左侧是品种树
        self.left_tree = QTreeWidget(clicked=self.variety_tree_clicked)
        self.left_tree.header().hide()
        self.left_tree.setMaximumWidth(160)
        llayout.addWidget(self.left_tree)
        layout.addLayout(llayout)
        # 右侧上下布局
        rlayout = QVBoxLayout(spacing=10)
        # 所属品种
        attach_varieties_layout = QHBoxLayout()
        attach_varieties_layout.addWidget(QLabel('所属品种:'))
        self.attach_varieties = QLabel()
        self.attach_varieties.variety_ids = list()  # id字符串
        attach_varieties_layout.addWidget(self.attach_varieties)
        attach_varieties_layout.addStretch()
        attach_varieties_layout.addWidget(QPushButton('清空', objectName='deleteBtn', cursor=Qt.PointingHandCursor,
                                                      clicked=self.clear_attach_varieties), alignment=Qt.AlignRight)
        rlayout.addLayout(attach_varieties_layout)
        # 所属分类
        attach_category_layout = QHBoxLayout()
        attach_category_layout.addWidget(QLabel('所属分类:'))
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(400)
        attach_category_layout.addWidget(self.category_combo)
        attach_category_layout.addStretch()
        rlayout.addLayout(attach_category_layout)
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("报告日期:", self))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        rlayout.addLayout(date_layout)
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel('报告标题:', self))
        self.title_edit = QLineEdit(self)
        title_layout.addWidget(self.title_edit)
        rlayout.addLayout(title_layout)
        # 选择报告
        select_report_layout = QHBoxLayout()
        select_report_layout.addWidget(QLabel('报告文件:', self))
        self.report_file_edit = FilePathLineEdit()
        self.report_file_edit.setParent(self)
        select_report_layout.addWidget(self.report_file_edit)
        rlayout.addLayout(select_report_layout)
        # 提交按钮
        self.commit_button = QPushButton('提交', clicked=self.commit_upload_report)
        rlayout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        rlayout.addStretch()
        layout.addLayout(rlayout)
        self.setLayout(layout)
        self.setFixedSize(800, 500)
        self.setStyleSheet("""
        #deleteBtn{
            border: none;
            color:rgb(200,100,80)
        }
        #newCategoryBtn{
            border:none;
            color:rgb(80,100,200)
        }
        """)
        self.geTreeVarieties()
        for category_item in [("日报", 1), ("周报", 2), ("月报", 3), ("年报", 4), ("专题报告", 5), ("其他", 0)]:
            self.category_combo.addItem(category_item[0], category_item[1])

    def geTreeVarieties(self):
        # 填充品种树
        for group_item in self.variety_info:
            group = QTreeWidgetItem(self.left_tree)
            group.setText(0, group_item['name'])
            group.gid = group_item['id']
            # 添加子节点
            for variety_item in group_item['subs']:
                child = QTreeWidgetItem()
                child.setText(0, variety_item['name'])
                child.vid = variety_item['id']
                group.addChild(child)
        self.left_tree.expandAll()  # 展开所有

    # 清空所属品种
    def clear_attach_varieties(self):
        self.attach_varieties.setText('')
        self.attach_varieties.variety_ids.clear()  # id列表

    def commit_upload_report(self):
        data = dict()
        title = self.title_edit.text()
        file_path = self.report_file_edit.text()
        if not all([title, file_path]):
            QMessageBox.information(self, "错误", "请填写完整信息")
            return
        data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        data['title'] = title
        data['link_varieties'] = ','.join(map(str, self.attach_varieties.variety_ids))
        data["custom_time"] = self.date_edit.text()
        data['category'] = self.category_combo.currentData()
        # 读取文件
        file = open(file_path, "rb")
        file_content = file.read()
        file.close()
        filename = file_path.rsplit('/', 1)[1]
        # 文件内容字段
        data["report_file"] = (filename,file_content)
        encode_data = encode_multipart_formdata(data)
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'report/',
                headers={"Content-Type": encode_data[1]},
                data=encode_data[0]
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            QMessageBox.information(self, "成功", "添加报告成功")
            self.close()

    # 点击左侧品种树
    def variety_tree_clicked(self):
        item = self.left_tree.currentItem()
        if item.childCount():  # has children open the root
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
        text = item.text(0)
        if item.parent() and item.vid not in self.attach_varieties.variety_ids:  # 所属品种中增加当前品种
            self.attach_varieties.setText(self.attach_varieties.text() + text + '、')
            self.attach_varieties.variety_ids.append(item.vid)


# 常规报告表格
class ReportTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(ReportTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)

    def setRowContents(self, contents):
        self.clear()
        table_headers = ['序号', '日期', '标题']
        self.setColumnCount(len(table_headers))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.setRowCount(len(contents))
        for row, row_item in enumerate(contents):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            item0.file_url = row_item['file_url']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['custom_time'])
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
            view_action.triggered.connect(self.view_report_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

        # super(ReportTable, self).mousePressEvent(event)  # 事件不再往外传了

    def view_report_detail(self):
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
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/report/' + str(itemid) + '/?utoken=' + settings.app_dawn.value("AUTHORIZATION")
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 常规报告
class NormalReportPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(NormalReportPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)
        # 分类选择、信息展示与新增按钮
        message_button_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        message_button_layout.addWidget(QLabel('类别:'))
        message_button_layout.addWidget(self.category_combo)
        message_button_layout.addWidget(QLabel('品种:'))
        self.variety_combo = QComboBox(activated=self.getCurrentReports)
        message_button_layout.addWidget(self.variety_combo)
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addStretch()  # 伸缩
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_new_report), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 当前数据显示表格
        self.report_table = ReportTable()
        # self.report_table.network_result.connect(self.network_message_label.setText)
        layout.addWidget(self.report_table)
        self.setLayout(layout)
        self.variety_info = []

    def getVariety(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'variety/?way=group',
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError("请求数据失败")
        except Exception as e:
            pass
        else:
            self.variety_info = response['variety']
            for index, group_item in enumerate(self.variety_info):
                self.category_combo.addItem(group_item['name'], group_item['id'])
                if index == 0:
                    for variety_item in group_item['subs']:
                        self.variety_combo.addItem(variety_item['name'], variety_item['id'])

    # 获取当前用户的报告
    def getCurrentReports(self):
        # 获取身份证明
        user_id = settings.app_dawn.value('UKEY', None)
        if not user_id:
            QMessageBox.warning(self, "错误", "软件内部发生错误.")
            return
        user_id = pickle.loads(user_id)
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/report/'
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText("获取报告失败!")
        else:
            self.report_table.setRowContents(response['reports'])
            self.network_message_label.setText("获取报告成功!")

    def create_new_report(self):
        popup = CreateReportPopup(variety_info=self.variety_info, parent=self)
        popup.exec_()


"""交易通知"""


# 新增交易通知
class CreateTransactionNoticePopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateTransactionNoticePopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(400, 150)
        self.setWindowTitle("新增通知")
        layout = QVBoxLayout(self)
        title_layout = QHBoxLayout(self)
        title_layout.addWidget(QLabel("通知标题:", self))
        self.title_edit = QLineEdit(self)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        category_layout = QHBoxLayout(self)
        category_layout.addWidget(QLabel("所属分类:", self))
        self.category_combobox = QComboBox(self)
        for category_item in [(1,"交易所"), (2,"公司"), (3, "系统"), (0, "其他")]:
            self.category_combobox.addItem(category_item[1], category_item[0])
        category_layout.addWidget(self.category_combobox)
        self.category_combobox.setMinimumWidth(200)
        category_layout.addStretch()
        layout.addLayout(category_layout)
        file_layout = QHBoxLayout(self)
        self.file_edit = FilePathLineEdit()
        self.file_edit.setParent(self)
        file_layout.addWidget(QLabel('通知文件:'))
        file_layout.addWidget(self.file_edit)
        layout.addLayout(file_layout)
        self.commit_button = QPushButton("提交", self)
        self.commit_button.clicked.connect(self.commit_new_notice)
        layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def commit_new_notice(self):
        data = dict()
        title = self.title_edit.text().strip()
        file_path = self.file_edit.text()
        if not all([title, file_path]):
            QMessageBox.information(self, "错误", "请填写完整信息")
            return
        data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
        data['title'] = title
        data['category'] = self.category_combobox.currentData()
        # 读取文件
        file = open(file_path, "rb")
        file_content = file.read()
        file.close()
        filename = file_path.rsplit('/', 1)[1]
        # 文件内容字段
        data["notice_file"] = (filename, file_content)
        encode_data = encode_multipart_formdata(data)
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'exnotice/',
                headers={"Content-Type": encode_data[1]},
                data=encode_data[0]
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            QMessageBox.information(self, "成功", "添加通知成功")
            self.close()


# 交易通知表格
class TransactionNoticeTable(QTableWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(TransactionNoticeTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)

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
            view_action.triggered.connect(self.view_notice_detail)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

        # super(ReportTable, self).mousePressEvent(event)  # 事件不再往外传了

    def view_notice_detail(self):
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
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/exnotice/' + str(
                    itemid) + '/?utoken=' + settings.app_dawn.value("AUTHORIZATION")
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 交易通知管理页面
class TransactionNoticePage(QWidget):
    def __init__(self, *args, **kwargs):
        super(TransactionNoticePage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)
        # 分类选择、信息展示与新增按钮
        message_button_layout = QHBoxLayout()
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addStretch()  # 伸缩
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_transaction_notice), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 当前数据显示表格
        self.notice_table = TransactionNoticeTable()
        self.notice_table.network_result.connect(self.network_message_label.setText)
        layout.addWidget(self.notice_table)
        self.setLayout(layout)

    # 获取当前交易通知
    def getCurrentTransactionNotce(self):
        try:
            user_id = pickle.loads(settings.app_dawn.value("UKEY"))
            # 发起请求当前数据
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/'+str(user_id)+'/exnotice/',
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.notice_table.showRowContents(response['exnotices'])
            self.network_message_label.setText(response['message'])

    # 新建交易通知
    def create_transaction_notice(self):
        popup = CreateTransactionNoticePopup(parent=self)
        popup.exec_()


"""现货报表"""


class EditSpotMessageWidget(QWidget):
    commit_successful = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(EditSpotMessageWidget, self).__init__(*args,**kwargs)
        layout = QVBoxLayout(self)
        date_layout = QHBoxLayout(self)
        date_layout.addWidget(QLabel("日期:", self))
        self.custom_time_edit = QDateEdit(QDate.currentDate(),parent=self)
        self.custom_time_edit.setCalendarPopup(True)
        self.custom_time_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.custom_time_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        name_layout= QHBoxLayout(self)
        name_layout.addWidget(QLabel("名称:", self))
        self.name_edit = QLineEdit(self)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        area_layout = QHBoxLayout(self)
        area_layout.addWidget(QLabel("地区:", self))
        self.area_edit = QLineEdit(self)
        area_layout.addWidget(self.area_edit)
        layout.addLayout(area_layout)
        level_layout = QHBoxLayout(self)
        level_layout.addWidget(QLabel("等级:", self))
        self.level_edit = QLineEdit(self)
        level_layout.addWidget(self.level_edit)
        layout.addLayout(level_layout)
        price_layout = QHBoxLayout(self)
        price_layout.addWidget(QLabel("价格:", self))
        self.price_edit = QLineEdit(self)
        decimal_validator = QRegExpValidator(QRegExp(r"[-]{0,1}[0-9]+[.]{1}[0-9]+"))
        self.price_edit.setValidator(decimal_validator)
        price_layout.addWidget(self.price_edit)
        layout.addLayout(price_layout)
        increase_layout = QHBoxLayout(self)
        increase_layout.addWidget(QLabel("增减:", self))
        self.increase_edit = QLineEdit(self)
        self.increase_edit.setValidator(decimal_validator)
        increase_layout.addWidget(self.increase_edit)
        layout.addLayout(increase_layout)
        self.commit_button = QPushButton("确认提交", self)
        self.commit_button.clicked.connect(self.commit_spot)
        layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def commit_spot(self):
        date = self.custom_time_edit.text()
        name = self.name_edit.text().strip()
        area = self.area_edit.text().strip()
        level = self.level_edit.text().strip()
        price = self.price_edit.text().strip()
        increase = self.increase_edit.text().strip()
        if not all([name,level,price]):
            QMessageBox.information(self, "错误", "请填写完整信息")
            return
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'spot/',
                headers={"Content-Type":"application/json;charset=utf8"},
                data=json.dumps({
                    'utoken': settings.app_dawn.value('AUTHORIZATION'),
                    'custom_time': date,
                    'name':name,
                    'area':area,
                    'level':level,
                    'price':price,
                    'increase':increase
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])

        except Exception as e:
            QMessageBox.information(self,'错误', str(e))
        else:

            QMessageBox.information(self, "成功",response['message'])
            self.commit_successful.emit()


# 新增现货报表
class CreateNewSpotTablePopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewSpotTablePopup, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        self.setFixedSize(300, 280)
        self.setWindowTitle("现货数据")
        self.setAttribute(Qt.WA_DeleteOnClose)
        title_layout = QHBoxLayout(self)
        title_layout.addStretch()
        title_layout.addWidget(QPushButton("模板下载", self, objectName='downloadModel', clicked=self.download_model_file))
        title_layout.addWidget(QPushButton("批量上传", self, objectName='uploadfile', clicked=self.upload_file))
        layout.addLayout(title_layout)
        self.edit_widget = EditSpotMessageWidget()
        self.edit_widget.setParent(self)
        self.edit_widget.commit_successful.connect(self.close)
        layout.addWidget(self.edit_widget)
        self.setLayout(layout)
        self.setStyleSheet("""
        #downloadModel{
            border: none;
            color:rgb(20,150,200)
        }
        #downloadModel:pressed{
            color: red;
        }
        #downloadModel:hover{
            color: rgb(20, 180, 200)
        }
        """)

    def upload_file(self):
        self.edit_widget.commit_button.setEnabled(False)
        self.edit_widget.commit_button.setText("处理文件")
        upload_file_path, _ = QFileDialog.getOpenFileName(self, '打开表格', '', "Excel file(*.xls *xlsx)")
        if upload_file_path:
            data = dict()
            data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
            f = open(upload_file_path,'rb')
            file_content = f.read()
            f.close()
            filename = upload_file_path.rsplit('/',1)[1]
            data['spot_file'] = (filename, file_content)
            encode_data = encode_multipart_formdata(data)
            try:
                r = requests.post(
                    url=settings.SERVER_ADDR + 'spot/',
                    headers={"Content-Type": encode_data[1]},
                    data=encode_data[0]
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 201:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(self, "错误", str(e))
                self.edit_widget.commit_button.setEnabled(True)
                self.edit_widget.commit_button.setText("确认提交")
            else:
                QMessageBox.information(self, "成功", "上传数据成功")
                self.edit_widget.commit_button.setEnabled(True)
                self.edit_widget.commit_button.setText("确认提交")
                self.close()

    # 下载数据模板
    def download_model_file(self):
        directory = QFileDialog.getExistingDirectory(None, '保存到', os.getcwd())
        # 请求模板文件信息，保存
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'model_files/?filename=spot_file_model.xlsx')
            save_path = os.path.join(directory, '现货报表模板.xlsx')
            if r.status_code != 200:
                raise ValueError('下载模板错误.')
            with open(save_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            pass


# 现货报表管理表格
class SpotCommodityTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(SpotCommodityTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ['序号','日期', '名称', '地区', '等级', '价格', '增减']
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row, row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row,0,item0)
            item1 = QTableWidgetItem(row_item['custom_time'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['name'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['area'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['level'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)
            item5 = QTableWidgetItem(row_item['price'])
            item5.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 5, item5)
            item6 = QTableWidgetItem(row_item['increase'])
            item6.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 6, item6)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/spot/' + str(
                    itemid) + '/?utoken=' + settings.app_dawn.value("AUTHORIZATION")
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 现货报表管理页面
class SpotCommodityPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(SpotCommodityPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)
        # 日期选择、信息展示与新增按钮
        message_button_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate(), dateChanged=self.getCurrentSpotCommodity)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        message_button_layout.addWidget(QLabel('日期:'))
        message_button_layout.addWidget(self.date_edit)
        self.network_message_label = QLabel()
        message_button_layout.addWidget(self.network_message_label)
        message_button_layout.addStretch()  # 伸缩
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_spot_table), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 当前数据显示表格
        self.spot_table = SpotCommodityTable()
        layout.addWidget(self.spot_table)
        self.setLayout(layout)

        # 上传数据的进度条
        self.process_widget = QWidget(self)
        self.process_widget.resize(self.width(), self.height())
        process_layout = QVBoxLayout(self.process_widget)
        process_layout.addStretch()
        self.process_message = QLabel("数据上传处理中..", self.process_widget)
        process_layout.addWidget(self.process_message)
        process = QProgressBar(parent=self.process_widget)
        process.setMinimum(0)
        process.setMaximum(0)
        process.setTextVisible(False)
        process_layout.addWidget(process)
        process_layout.addStretch()
        self.process_widget.setLayout(process_layout)
        self.process_widget.hide()
        self.process_widget.setStyleSheet("background:rgb(200,200,200);opacity:0.6")

    # 获取当前时间的现货报表
    def getCurrentSpotCommodity(self):
        current_date = self.date_edit.text()
        current_page = 1
        try:
            user_id = pickle.loads(settings.app_dawn.value("UKEY"))
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/'+str(user_id) + '/spot/?page=' +str(current_page) +'&page_size=50&date=' + current_date
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_message_label.setText(str(e))
        else:
            self.spot_table.showRowContents(response['spots'])
            self.network_message_label.setText(response['message'])

    # 新增现货报表数据
    def create_spot_table(self):
        popup = CreateNewSpotTablePopup(parent=self)
        popup.exec_()


"""财经日历"""


class EditFinanceCalendarWidget(QWidget):
    def __init__(self):
        super(EditFinanceCalendarWidget, self).__init__()
        layout = QVBoxLayout(margin=0)
        layout.setParent(self)
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日期:", self))
        self.date_edit = QDateEdit(QDate.currentDate(), self)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("时间:", self))
        self.time_edit = QTimeEdit(QTime.currentTime(),self)
        self.time_edit.setDisplayFormat('hh:mm:ss')
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel('地区:', self))
        self.area_edit = QLineEdit(self)
        area_layout.addWidget(self.area_edit)
        layout.addLayout(area_layout)
        event_layout = QHBoxLayout()
        event_layout.addWidget(QLabel('事件:', self), alignment=Qt.AlignTop)
        self.event_edit = QTextEdit(self)
        self.event_edit.setFixedHeight(100)
        event_layout.addWidget(self.event_edit)
        layout.addLayout(event_layout)
        expected_layout = QHBoxLayout()
        expected_layout.addWidget(QLabel('预期值:', self))
        self.expected_edit = QLineEdit(self)
        expected_layout.addWidget(self.expected_edit)
        layout.addLayout(expected_layout)
        self.commit_button = QPushButton("提交", self)
        self.commit_button.clicked.connect(self.commit_financial_calendar)
        layout.addWidget(self.commit_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def commit_financial_calendar(self):
        date = self.date_edit.text().strip()
        time = self.time_edit.text().strip()
        area = self.area_edit.text().strip()
        event = self.event_edit.toPlainText()
        expected = self.expected_edit.text().strip()

        if not all([date,time,area,event]):
            QMessageBox.information(self, "错误", "请填写完整信息")
            return
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'fecalendar/',
                headers={"Content-Type":"application/json;charset=utf8"},
                data=json.dumps({
                    'utoken': settings.app_dawn.value('AUTHORIZATION'),
                    'date': date,
                    'time':time,
                    'country':area,
                    'event':event,
                    'expected':expected,
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self,'错误', str(e))
        else:

            QMessageBox.information(self, "成功",response['message'])


# 新增财经日历
class CreateNewFinanceCalendarPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewFinanceCalendarPopup, self).__init__(*args, **kwargs)
        self.setFixedSize(300, 280)
        self.setWindowTitle("财经日历")
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout()
        option_layout = QHBoxLayout()
        option_layout.addStretch()
        self.download_model_button = QPushButton("模板下载", self, objectName='downloadModel', clicked=self.download_model_file)
        option_layout.addWidget(self.download_model_button)
        self.option_button = QPushButton("批量上传", self, clicked=self.upload_file)
        option_layout.addWidget(self.option_button)
        layout.addLayout(option_layout)
        self.edit_widget = EditFinanceCalendarWidget()
        self.edit_widget.setParent(self)
        layout.addWidget(self.edit_widget)
        self.setLayout(layout)
        self.setStyleSheet("""
        #downloadModel{
            border: none;
            color:rgb(20,150,200)
        }
        #downloadModel:pressed{
            color: red;
        }
        #downloadModel:hover{
            color: rgb(20, 180, 200)
        }
        """)

    def upload_file(self):
        self.edit_widget.commit_button.setEnabled(False)
        self.edit_widget.commit_button.setText("处理文件")
        upload_file_path, _ = QFileDialog.getOpenFileName(self, '打开表格', '', "Excel file(*.xls *xlsx)")
        if upload_file_path:
            data = dict()
            data['utoken'] = settings.app_dawn.value('AUTHORIZATION')
            f = open(upload_file_path, 'rb')
            file_content = f.read()
            f.close()
            filename = upload_file_path.rsplit('/', 1)[1]
            data['fecalendar_file'] = (filename, file_content)
            encode_data = encode_multipart_formdata(data)
            try:
                r = requests.post(
                    url=settings.SERVER_ADDR + 'fecalendar/',
                    headers={"Content-Type": encode_data[1]},
                    data=encode_data[0]
                )
                response = json.loads(r.content.decode('utf8'))
                if r.status_code != 201:
                    raise ValueError(response['message'])
            except Exception as e:
                QMessageBox.information(self, "错误", str(e))
                self.edit_widget.commit_button.setEnabled(True)
                self.edit_widget.commit_button.setText("确认提交")
            else:
                QMessageBox.information(self, "成功", "上传数据成功")
                self.edit_widget.commit_button.setEnabled(True)
                self.edit_widget.commit_button.setText("确认提交")
                self.close()

    # 下载数据模板
    def download_model_file(self):
        directory = QFileDialog.getExistingDirectory(None, '保存到', os.getcwd())
        # 请求模板文件信息，保存
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'model_files/?filename=finance_calendar_model.xlsx')
            save_path = os.path.join(directory, '财经日历模板.xlsx')
            if r.status_code != 200:
                raise ValueError('下载模板错误.')
            with open(save_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            pass


# 财经日历显示表格
class FinanceCalendarTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(FinanceCalendarTable, self).__init__(*args, **kwargs)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)

    def showRowContents(self, row_list):
        self.clear()
        table_headers = ["序号","日期", "时间", "事件", "预期值"]
        self.setColumnCount(len(table_headers))
        self.setRowCount(len(row_list))
        self.setHorizontalHeaderLabels(table_headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for row,row_item in enumerate(row_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.id = row_item['id']
            self.setItem(row, 0, item0)
            item1 = QTableWidgetItem(row_item['date'])
            item1.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, item1)
            item2 = QTableWidgetItem(row_item['time'])
            item2.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 2, item2)
            item3 = QTableWidgetItem(row_item['event'])
            item3.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, item3)
            item4 = QTableWidgetItem(row_item['expected'])
            item4.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, item4)

    def mousePressEvent(self, event):
        index = self.indexAt(QPoint(event.pos().x(), event.pos().y()))
        row, _ = index.row(), index.column()
        if row < 0:
            return
        self.setCurrentIndex(index)
        if event.buttons() == Qt.RightButton:
            rmenu = QMenu()
            rmenu.setAttribute(Qt.WA_DeleteOnClose)
            delete_action = rmenu.addAction("删除")
            delete_action.triggered.connect(self.delete_row_record)
            rmenu.exec_(QCursor.pos())

    def delete_row_record(self):
        delete_action = QMessageBox.warning(self, "提示", "删除将不可恢复!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if delete_action != QMessageBox.Yes:
            return
        row = self.currentRow()
        itemid = self.item(row, 0).id
        try:
            user_id = pickle.loads(settings.app_dawn.value('UKEY'))
            r = requests.delete(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/fecalendar/' + str(
                    itemid) + '/?utoken=' + settings.app_dawn.value("AUTHORIZATION")
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            QMessageBox.information(self, "错误", str(e))
        else:
            self.removeRow(row)
            QMessageBox.information(self, "成功", '删除成功!')


# 财经日历管理页面
class FinanceCalendarPage(QWidget):

    def __init__(self, *args, **kwargs):
        super(FinanceCalendarPage, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0, spacing=2)

        # 日期选择、信息展示与新增按钮
        message_button_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate(), dateChanged=self.getCurrentFinanceCalendar)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        message_button_layout.addWidget(QLabel('日期:'))
        message_button_layout.addWidget(self.date_edit)
        message_button_layout.addStretch()  # 伸缩
        message_button_layout.addWidget(QPushButton('新增', clicked=self.create_finance_calendar), alignment=Qt.AlignRight)
        layout.addLayout(message_button_layout)
        # 当前数据显示表格
        self.finance_table = FinanceCalendarTable()
        layout.addWidget(self.finance_table)
        self.setLayout(layout)

    # 获取当前日期财经日历
    def getCurrentFinanceCalendar(self):
        current_date = self.date_edit.text()
        current_page = 1
        try:
            user_id = pickle.loads(settings.app_dawn.value("UKEY"))
            r = requests.get(
                url=settings.SERVER_ADDR + 'user/' + str(user_id) + '/fecalendar/?page=' +str(current_page)+'&page_size=50&date=' + current_date,

            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            self.finance_table.showRowContents(response['fecalendar'])

    # 新增财经日历数据
    def create_finance_calendar(self):
        popup = CreateNewFinanceCalendarPopup(parent=self)
        if not popup.exec_():
            self.getCurrentFinanceCalendar()


# 首页管理主页
class HomePageAdmin(QWidget):
    network_result = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(HomePageAdmin, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)

        # 左侧菜单列表
        self.left_list = QListWidget(parent=self, clicked=self.left_menu_clicked)
        layout.addWidget(self.left_list, alignment=Qt.AlignLeft)
        # 右侧显示具体操作窗体
        self.operate_frame = LoadedPage()
        self.operate_frame.remove_borders()
        layout.addWidget(self.operate_frame)
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

    # 添加菜单按钮
    def add_left_menus(self):
        # 获取身份证明
        user_key = settings.app_dawn.value('UROLE')
        user_key = pickle.loads(user_key)
        if user_key <= 3:  # 信息管理以上
            actions = [u'新闻公告', u'常规报告', u'交易通知', u'现货报表', u'财经日历']
        else:
            actions = [u'常规报告']
        for item in actions:
            self.left_list.addItem(item)

    # 点击左侧按钮
    def left_menu_clicked(self):
        text = self.left_list.currentItem().text()
        if text == u'新闻公告':
            frame_page = NewsBulletinPage()
            frame_page.getNewsBulletins()
        elif text == u'常规报告':
            frame_page = NormalReportPage()
            frame_page.getVariety()
            frame_page.getCurrentReports()
        elif text == u'交易通知':
            frame_page = TransactionNoticePage()
            frame_page.getCurrentTransactionNotce()
        elif text == u'现货报表':
            frame_page = SpotCommodityPage()
            frame_page.getCurrentSpotCommodity()
        elif text == u'财经日历':
            frame_page = FinanceCalendarPage()
            frame_page.getCurrentFinanceCalendar()
        else:
            frame_page = QLabel('【' + text + '】正在加紧开发中...')
        self.operate_frame.clear()
        self.operate_frame.addWidget(frame_page)
