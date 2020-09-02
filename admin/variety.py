# _*_ coding:utf-8 _*_
# @File  : variety.py
# @Time  : 2020-08-10 13:42
# @Author: zizle
import re
import json
from PyQt5.QtWidgets import qApp, QListWidgetItem, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from .variety_ui import VarietyAdminUI
from settings import SERVER_API


class VarietyAdmin(VarietyAdminUI):

    def __init__(self, *args, **kwargs):
        super(VarietyAdmin, self).__init__(*args, **kwargs)
        # 添加品种组别的选项
        for group in [
            {"name": "金融股指", "name_en": "finance", "logo": "media/icons/finance.png"},
            {"name": "农副产品", "name_en": "farm", "logo": "media/icons/farm_product.png"},
            {"name": "能源化工", "name_en": "chemical", "logo": "media/icons/chemical.png"},
            {"name": "金属产业", "name_en": "metal", "logo": "media/icons/metal.png"}
        ]:
            group_item = QListWidgetItem(group["name"])
            group_item.setIcon(QIcon(group["logo"]))
            setattr(group_item, "name_en", group["name_en"])
            self.group_list.addItem(group_item)

            self.opts_widget.belong_group.addItem(group["name"], group["name_en"])  # 添加新建品种页面的组别选项

        # 添加新建品种页面的交易所选项
        for exchange in [
            {"name": "郑州商品交易所", "name_en": "czce"},
            {"name": "大连商品交易所", "name_en": "dce"},
            {"name": "上海期货交易所", "name_en": "shfe"},
            {"name": "中国金融期货交易所", "name_en": "cffex"}
        ]:
            self.opts_widget.belong_exchange.addItem(exchange["name"], exchange["name_en"])

        self.group_list.clicked.connect(self.select_variety_group)                   # 点击项目的行为
        self.opts_widget.add_button.clicked.connect(self.add_new_variety)            # 新建品种与列表显示切换
        self.opts_widget.commit_new_button.clicked.connect(self.commit_new_variety)  # 确定新增品种

    def select_variety_group(self):
        """ 点击选择了品种组 """
        current_group_item = self.group_list.currentItem()
        group_name_en = getattr(current_group_item, "name_en")
        # 获取该组下的所有品种
        self.get_current_group_variety(group_name_en)

    def get_current_group_variety(self, group_text):
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'variety/?group=' + group_text
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.current_group_variety_reply)

    def current_group_variety_reply(self):
        """ 获取当前组的品种返回 """
        reply = self.sender()
        if reply.error():
            varieties = []
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            varieties = data["varieties"]
        reply.deleteLater()
        # 表格显示
        self.group_variety_table_content(varieties)

    def group_variety_table_content(self, varieties):
        self.variety_table.clear()
        headers = ["品种名称", "交易代码", "交易所", "组别"]
        self.variety_table.setColumnCount(len(headers))
        self.variety_table.setRowCount(len(varieties))
        self.variety_table.setHorizontalHeaderLabels(headers)
        for row, variety_item in enumerate(varieties):
            self.variety_table.setRowHeight(row, 25)
            item0 = QTableWidgetItem(variety_item["variety_name"])
            item0.setTextAlignment(Qt.AlignCenter)
            self.variety_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(variety_item["variety_en"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.variety_table.setItem(row, 1, item1)
            item2 = QTableWidgetItem(variety_item["exchange_lib"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.variety_table.setItem(row, 2, item2)
            item3 = QTableWidgetItem(variety_item["group_name"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.variety_table.setItem(row, 3, item3)

    def add_new_variety(self):
        """ 新建品种与列表显示切换 """
        button = self.sender()
        if button.text() == "新建品种":
            button.setText("品种列表")
            self.variety_table.hide()
            self.opts_widget.new_variety_widget.show()
        else:
            button.setText("新建品种")
            self.opts_widget.new_variety_widget.hide()
            self.variety_table.show()

    def commit_new_variety(self):
        """ 确认提交新品种信息 """
        belong_group = self.opts_widget.belong_group.currentData()
        belong_exchange = self.opts_widget.belong_exchange.currentData()
        variety_name = self.opts_widget.zh_name.text().strip()
        variety_en = self.opts_widget.en_name.text().strip()
        if not re.match(r'^[A-Z]{1,2}$', variety_en):
            QMessageBox.information(self, "错误", "交易代码为1~2个A-Z大写英文字母组成!")
            return

        new_variety = {
            "variety_name": variety_name,
            "variety_en": variety_en,
            "exchange_lib": belong_exchange,
            "group_name": belong_group
        }

        network_manager = getattr(qApp, "_network")

        url = SERVER_API + 'variety/'
        request = QNetworkRequest(QUrl(url))
        reply = network_manager.post(request, json.dumps(new_variety).encode('utf-8'))
        reply.finished.connect(self.commit_variety_reply)

    def commit_variety_reply(self):
        """ 提交新品种信息返回 """
        reply = self.sender()
        if reply.error() == QNetworkReply.ProtocolInvalidOperationError:
            QMessageBox.information(self, "错误", "添加品种失败:\n名称和交易代码联合完全重复了!")
        elif reply.error() == QNetworkReply.InternalServerError:
            QMessageBox.information(self, "错误", "服务器发生了个错误,添加失败!")
        else:
            if reply.error() == QNetworkReply.NoError:
                QMessageBox.information(self, "成功", "添加新品种成功!")
        reply.deleteLater()

