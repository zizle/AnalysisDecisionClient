# _*_ coding:utf-8 _*_
# @File  : user_data.py
# @Time  : 2020-09-03 14:12
# @Author: zizle
""" 用户产业数据模块后台维护 """
import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import qApp, QListWidgetItem, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QBrush, QColor, QIcon
from settings import SERVER_API, logger, BASE_DIR
from utils.client import get_user_token, get_client_uuid
from popup.industry_popup import UpdateFolderPopup, DisposeChartPopup
from popup.sheet_charts import SheetChartsPopup, DeciphermentPopup, ChartPopup
from popup.message import InformationPopup, WarningPopup
from .user_data_ui import UserDataMaintainUI, SheetChartUI, OperateButton

pd.set_option('mode.chained_assignment', None)  # pandas不提示警告


class UpdatingSheetsThread(QThread):
    """ 更新数据表的线程 """
    single_finished = pyqtSignal(int)  # 单个完成的信号(2020-09-04预留更新进度条使用)

    def __init__(self, variety_en, group_id, path_list, *args, **kwargs):
        super(UpdatingSheetsThread, self).__init__(*args, **kwargs)
        self.variety_en = variety_en
        self.group_id = group_id
        self.path_list = path_list
        self.network_manager = getattr(qApp, '_network')

    def run(self):
        """ 读取数据,清洗数据 """
        for index, excel_path in enumerate(self.path_list):
            try:
                excel_file = pd.ExcelFile(excel_path)
            except Exception as e:
                logger.error("打开Excel文件失败:{}".format(e))
                continue
            for sheet_name in excel_file.sheet_names:
                if sheet_name.strip().lower().startswith("sheet"):
                    continue
                time.sleep(0.03)
                # converters参数 第0列为时间格式
                sheet_df = excel_file.parse(sheet_name=sheet_name, skiprows=[0], converters={0: self.date_converter})
                sheet_df.iloc[:1] = sheet_df.iloc[:1].fillna('')  # 替换第一行中有的nan
                # 替换除第一列以外的nan为空(这里直接inplace=True填充失败(原因:未知))
                sheet_df.iloc[:, 1:sheet_df.shape[1]] = sheet_df.iloc[:, 1:sheet_df.shape[1]].fillna('')
                sheet_df.dropna(axis=0, how='any', inplace=True)  # 删除含nan的行
                if sheet_df.empty:  # 处理后为空的数据继续下一个
                    continue
                sheet_df = sheet_df.applymap(str)
                # 读取数据的表头
                sheet_headers = sheet_df.columns.values.tolist()
                # 生成新的columns名称
                sheet_df.columns = ["column_{}".format(i) for i in range(len(sheet_headers))]
                # 将数据转为dict
                sheet_source = {
                    "variety_en": self.variety_en,
                    "group_id": self.group_id,
                    "sheet_name": sheet_name.strip(),
                    "sheet_headers": sheet_headers,
                    "sheet_values": sheet_df.to_dict(orient="records")
                }
                # 数据json化检验
                try:
                    json.dumps(sheet_source)
                except Exception:
                    logger.error("sheet:{} of file:{} encoder json fail!".format(sheet_name, excel_path))
                    continue
                self.to_server_updating(sheet_source)
            excel_file.close()
            self.single_finished.emit(index + 1)

    @staticmethod
    def date_converter(column_content):
        """ 时间类型转换器 """
        if isinstance(column_content, datetime):
            return column_content.strftime("%Y-%m-%d")
        else:
            return np.nan

    def to_server_updating(self, source_data):
        """ 将数据上传到服务器进行更新 """
        url = SERVER_API + "variety/{}/sheet/".format(self.variety_en)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = self.network_manager.post(request, json.dumps(source_data).encode("utf-8"))
        reply.finished.connect(self.sheet_data_server_reply)
        self.exec_()  # 开启事件循环才能接受到返回的信号,必须再reply之后

    def sheet_data_server_reply(self):
        """ 数据上传到服务器返回 """
        reply = self.sender()
        if reply.error() == QNetworkReply.AuthenticationRequiredError:
            logger.error("登录过期或没有品种权限,更新数据失败!")
        if reply.error() == QNetworkReply.ProtocolInvalidOperationError:
            logger.error("提交的数据内容有误,更新失败!")
        if reply.error():
            logger.error("其他未知情况,更新数据失败:{}".format(reply.error()))
        reply.deleteLater()
        self.quit()  # 事件循环退出，继续下一个


class UserDataMaintain(UserDataMaintainUI):
    def __init__(self, *args, **kwargs):
        super(UserDataMaintain, self).__init__(*args, **kwargs)

        self.is_ready = False  # 左侧菜单选择时是否请求品种下的数据组

        for menu_item in [
            {"name": "数据源配置", "name_en": "source_config"},
            {"name": "品种数据表", "name_en": "variety_sheet"},
            {"name": "我的数据图", "name_en": "sheet_chart"},
        ]:
            menu = QListWidgetItem(menu_item["name"])
            menu.setData(Qt.UserRole, menu_item["name_en"])
            self.maintain_menu.addItem(menu)

        self.maintain_menu.clicked.connect(self.selected_maintain_menu)  # 选择操作菜单
        self.source_config_widget.confirm_group_button.clicked.connect(self.create_new_sheet_group)  # 确定新增分组
        # 数据源配置页品种选择变化信号连接(请求当前品种下的分组)
        self.source_config_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        # 数据表显示页品种选择变化信号连接放在请求完品种权限返回添加完数据之后(不在__init__内连接信号可以减少一次请求分组的网络)
        # 数据图形显示页品种选择变化信号连接放在请求完品种权限返回添加完数据之后(不在__init__内连接信号可以减少一次请求分组的网络)

        self._get_user_variety()  # 获取用户有权限的品种(置于信号连接之后确保首次信号执行)

        self.source_config_widget.new_config_button.clicked.connect(self.config_update_folder)  # 调整配置更新文件夹
        self.source_config_widget.group_combobox.currentTextChanged.connect(self.show_groups_folder_list)  # 显示品种组的更新文件夹
        self.variety_sheet_widget.group_combobox.currentIndexChanged.connect(self.get_show_variety_sheets)  # 获取品种的数据表
        self.variety_sheet_widget.sheet_table.cellDoubleClicked.connect(self.popup_option_chart)  # 双击弹窗设置数据图
        self.variety_sheet_widget.sheet_table.cellChanged.connect(self.sheet_table_cell_changed)  # 数据表格变化
        self.variety_sheet_widget.only_me_check.stateChanged.connect(self.get_show_variety_sheets)# 重新获取品种的数据表

        self.sheet_chart_widget.swap_tab.tabBarClicked.connect(self.swap_to_render_variety_charts)  # 切换渲染品种下的图形
        self.sheet_chart_widget.chart_table.cellChanged.connect(self.chart_table_cell_changed)    # 图形表单元格变化
        self.sheet_chart_widget.only_me_check.stateChanged.connect(self.chart_page_variety_changed)  # 重新请求图形界面的图形

    def _get_user_variety(self):
        """ 获取用户有权限的品种信息 """
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/variety-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_variety_reply)

    def user_variety_reply(self):
        """ 获取用户的品种权限返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            pass
        else:
            data = json.loads(data.decode("utf-8"))
            current_user = data.get("user")
            if not current_user:
                logger.error("登录过期了,用户获取有权限的品种失败!")
                return
            self._combobox_allow_varieties(data["varieties"])
        reply.deleteLater()

    def _combobox_allow_varieties(self, varieties):
        today_str = datetime.today().strftime("%Y-%m-%d")
        for variety_item in varieties:
            if not variety_item["expire_date"] or variety_item["expire_date"] <= today_str:
                continue
            # 数据源配置页
            self.source_config_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 数据表显示页
            self.variety_sheet_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])
            # 品种图形显示页
            self.sheet_chart_widget.variety_combobox.addItem(variety_item["variety_name"], variety_item["variety_en"])

        # 数据表显示页品种选择变化(不在__init__内连接信号可以减少一次网络请求)
        self.variety_sheet_widget.variety_combobox.currentTextChanged.connect(self.variety_combobox_changed)
        # 数据图形显示页品种选择变化(不在__init__内连接信号可以减少一次网络请求)
        self.sheet_chart_widget.variety_combobox.currentTextChanged.connect(self.chart_page_variety_changed)
        self.is_ready = True

    def selected_maintain_menu(self):
        """ 选择了左侧菜单 """
        current_menu = self.maintain_menu.currentItem().data(Qt.UserRole)
        if current_menu == "source_config":
            self.maintain_frame.setCurrentIndex(0)
        elif current_menu == "variety_sheet":
            self.maintain_frame.setCurrentIndex(1)
        elif current_menu == "sheet_chart":
            self.maintain_frame.setCurrentIndex(2)
            self.chart_page_variety_changed()  # 手动调用请求品种的图形(否则第一次切换到图形页没有数据列表)
            return  # 图形界面无需再请求品种下的数据分组
        else:
            return
        if self.is_ready:
            self.variety_combobox_changed()  # 手动调用请求品种下的分组(否则第一次切换到品种表页面没有分组)

    def config_update_folder(self):
        """ 调整配置更新的文件夹 """
        variety_text, variety_en = self.source_config_widget.variety_combobox.currentText(), self.source_config_widget.variety_combobox.currentData()
        group_text, group_id = self.source_config_widget.group_combobox.currentText(), self.source_config_widget.group_combobox.currentData()
        if not all([variety_text, variety_en, group_text, group_id]):
            self.source_config_widget.tips_message.setText("选择正确的品种分组再配置.")
            return
        self.source_config_widget.tips_message.setText("")
        popup = UpdateFolderPopup(variety_text=variety_text, variety_en=variety_en, group_text=group_text, group_id=group_id, parent=self)
        popup.successful_signal.connect(self.config_folder_successfully)
        popup.exec_()

    def config_folder_successfully(self, text):
        """ 调整文件夹配置成功 """
        self.source_config_widget.tips_message.setText(text)
        self.sender().close()
        # 刷新
        self.show_groups_folder_list()

    def show_groups_folder_list(self):
        """ 显示组配置的更新文件夹 """
        variety_en, variety_text = self.source_config_widget.variety_combobox.currentData(), self.source_config_widget.variety_combobox.currentText()
        group_id = self.source_config_widget.group_combobox.currentData()
        client = get_client_uuid()
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "industry/user-folder/?variety_en={}&group_id={}&client={}".format(variety_en, group_id, client)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), get_user_token().encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.get_update_folders_reply)
        """
        # 为了用户重新安装不丢失更新文件夹，2020-09-29改为后端存储
        db_path = os.path.join(BASE_DIR, "dawn/local_data.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if group_id == 0:
            cursor.execute(
                "SELECT ID,VARIETY_EN,GROUP_ID,FOLDER FROM UPDATE_FOLDER WHERE VARIETY_EN=? AND CLIENT=?;",
                (variety_en, client)
            )
        else:
            cursor.execute(
                "SELECT ID,VARIETY_EN,GROUP_ID,FOLDER FROM UPDATE_FOLDER WHERE VARIETY_EN=? AND GROUP_ID=? AND CLIENT=?;",
                (variety_en, group_id, client)
            )
        folder_list = cursor.fetchall()
        cursor.close()
        conn.close()
        group_dict = dict()
        for i in range(self.source_config_widget.group_combobox.count()):
            group_dict[self.source_config_widget.group_combobox.itemData(i)] = self.source_config_widget.group_combobox.itemText(i)
        """
    def get_update_folders_reply(self):
        """ 获取更新文件夹返回 """
        reply = self.sender()
        if reply.error():
            folder_list = list()
        else:
            reply_message = json.loads(reply.readAll().data().decode("utf-8"))
            folder_list = reply_message["folders"]
        reply.deleteLater()
        self.source_config_widget.config_table.clearContents()
        self.source_config_widget.config_table.setRowCount(len(folder_list))
        for row, row_item in enumerate(folder_list):
            item0 = QTableWidgetItem(str(row + 1))
            item0.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["variety_name"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["group_name"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["folder"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.source_config_widget.config_table.setItem(row, 3, item3)

            item4_button = OperateButton("media/icons/update.png", "media/icons/update_hover.png", "点击更新", self.source_config_widget.config_table)
            setattr(item4_button, "row_index", row)
            item4_button.clicked.connect(self.updating_sheets_of_folder)
            self.source_config_widget.config_table.setCellWidget(row, 4, item4_button)

    def updating_sheets_of_folder(self):
        """ 更新文件夹内的所有数据表 """
        if self.source_config_widget.is_updating:
            self.source_config_widget.tips_message.setText("当前有数据正在更新,完成后再进行操作! ")
            return
        button_clicked = self.sender()
        current_row = getattr(button_clicked, "row_index")
        self.source_config_widget.config_table.selectRow(current_row)
        variety_en = self.source_config_widget.variety_combobox.currentData()
        group_text = self.source_config_widget.config_table.item(current_row, 2).text()
        folder_path = self.source_config_widget.config_table.item(current_row, 3).text()
        if not os.path.exists(folder_path):
            self.source_config_widget.tips_message.setText("文件夹路径不存在!")
            return
        group_id = None
        for i in range(self.source_config_widget.group_combobox.count()):
            if self.source_config_widget.group_combobox.itemText(i) == group_text:
                group_id = self.source_config_widget.group_combobox.itemData(i)
        if not group_id:
            self.source_config_widget.tips_message.setText("数据组别错误,无法更新数据!")
            return
        # 关闭按钮的点击事件
        button_clicked.setEnabled(False)
        # 开启数据更新的文字提示
        self.source_config_widget.tips_message.setText("正在更新数据,请稍候 ")
        self.source_config_widget.is_updating = True
        self.source_config_widget.current_button = button_clicked
        self.source_config_widget.updating_process.setMaximum(0)
        self.source_config_widget.updating_process.setValue(0)
        self.source_config_widget.updating_process.show()
        self.update_folder_sheets_to_server(variety_en, group_id, folder_path)

    def update_folder_sheets_to_server(self, variety_en, group_id, folder_path):
        """ 读取数据,更新数据到服务端 """
        file_path_list = list()
        for file_path in os.listdir(folder_path):
            filename, file_suffix = os.path.splitext(file_path)
            if filename.startswith("~$"):  # Excel的打开缓存文件
                continue
            if file_suffix in [".xlsx", '.xls']:
                file_path_list.append(os.path.join(folder_path, file_path))
        if not file_path_list:
            self.folder_update_finished(finished_status="没有获取到合法文件信息,无需更新!")
            return
        self.source_config_widget.updating_thread = UpdatingSheetsThread(variety_en=variety_en, group_id=group_id, path_list=file_path_list)
        self.source_config_widget.updating_thread.finished.connect(self.folder_update_finished)
        self.source_config_widget.updating_thread.single_finished.connect(self.source_config_widget.updating_process.setValue)
        self.source_config_widget.updating_thread.start()
        self.source_config_widget.updating_process.setMaximum(len(file_path_list))
        self.source_config_widget.updating_process.setValue(0)

    def folder_update_finished(self, finished_text="数据更新完成! "):
        """ 文件夹更新完毕 """
        if self.source_config_widget.updating_thread is not None:
            self.source_config_widget.updating_thread.deleteLater()
            self.source_config_widget.updating_thread = None
        self.source_config_widget.is_updating = False
        self.source_config_widget.tips_message.setText(finished_text)
        if self.source_config_widget.current_button is not None:
            self.source_config_widget.current_button.setEnabled(True)
        self.source_config_widget.updating_process.setMaximum(1)
        self.source_config_widget.updating_process.setValue(1)

    def variety_combobox_changed(self):
        """ 界面品种变化 """
        current_widget = self.maintain_frame.currentWidget()
        current_variety = current_widget.variety_combobox.currentData()
        if isinstance(current_widget, SheetChartUI):
            return
        self.get_variety_sheet_group(current_variety)

    def create_new_sheet_group(self):
        """ 创建新的品种数据分组 """
        group_name = self.source_config_widget.new_group_edit.text().strip()

        current_variety = self.source_config_widget.variety_combobox.currentData()
        if not all([group_name, current_variety]):
            return
        user_token = get_user_token()
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.post(request, json.dumps({"group_name": group_name}).encode("utf-8"))
        reply.finished.connect(self.variety_sheet_group_reply)

    def get_variety_sheet_group(self, current_variety):
        """ 获取品种下的数据分组 """
        url = SERVER_API + "variety/{}/sheet-group/".format(current_variety)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(request)
        reply.finished.connect(self.variety_sheet_group_reply)

    def variety_sheet_group_reply(self):
        """ 品种下的数据分组返回 """
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            logger.error("用户(新建时)获取数据分组失败:{}".format(data))
        else:
            self.source_config_widget.hide_create_new_group()
            current_widget = self.maintain_frame.currentWidget()
            data = json.loads(data.decode("utf-8"))
            current_widget.group_combobox.clear()
            current_widget.group_combobox.addItem("全部", 0)
            for group_item in data["groups"]:
                current_widget.group_combobox.addItem(group_item["group_name"], group_item["id"])
        reply.deleteLater()
        # 再次调用数据源配置页的查询已配置的文件夹内容项(由于变化了就连接信号,获取组不全需手动再次调用)
        self.show_groups_folder_list()

    """ 品种数据表界面 """

    def get_show_variety_sheets(self):
        """ 获取品种数据表 """
        variety_en = self.variety_sheet_widget.variety_combobox.currentData()
        group_id = self.variety_sheet_widget.group_combobox.currentData()
        is_own = 1 if self.variety_sheet_widget.only_me_check.checkState() else 0
        if group_id is None:
            return
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "variety/{}/sheet/?group_id={}&is_own={}".format(variety_en, group_id, is_own)
        request = QNetworkRequest(QUrl(url))
        user_token = get_user_token()
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.get_variety_sheets_reply)

    def get_variety_sheets_reply(self):
        """ 获取品种数据表返回了 """
        reply = self.sender()
        if reply.error():
            logger.error("用户获取品种数据表失败{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            self.show_variety_sheets(data["sheets"])
        reply.deleteLater()

    def show_variety_sheets(self, sheets):
        """ 显示当前条件下的品种表 """
        # 关闭表格单元格变化的信号
        self.variety_sheet_widget.sheet_table.cellChanged.disconnect()
        self.variety_sheet_widget.sheet_table.clear()
        if self.variety_sheet_widget.only_me_check.checkState():
            self.variety_sheet_widget.sheet_table.setColumnCount(11)
            self.variety_sheet_widget.sheet_table.setHorizontalHeaderLabels(
                ["编号", "创建日期", "创建人", "名称", "更新时间", "更新人", "增量", "图形", "上移", "删除","可见"]
            )
        else:
            self.variety_sheet_widget.sheet_table.setColumnCount(10)
            self.variety_sheet_widget.sheet_table.setHorizontalHeaderLabels(
                ["编号", "创建日期", "创建人", "名称", "更新时间", "更新人", "增量", "图形", "上移", "删除"]
            )
        self.variety_sheet_widget.sheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.variety_sheet_widget.sheet_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.variety_sheet_widget.sheet_table.setRowCount(len(sheets))

        for row, row_item in enumerate(sheets):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["create_date"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["creator"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["sheet_name"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(row_item["update_date"])
            item4.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 4, item4)

            item5 = QTableWidgetItem(row_item["update_by"])
            item5.setTextAlignment(Qt.AlignCenter)
            self.variety_sheet_widget.sheet_table.setItem(row, 5, item5)

            update_count = row_item["update_count"]
            item6 = QTableWidgetItem(str(update_count))
            item6.setTextAlignment(Qt.AlignCenter)
            item6.setForeground(QBrush(QColor(233, 66, 66))) if update_count > 0 else item6.setForeground(QBrush(QColor(66, 66, 66)))
            self.variety_sheet_widget.sheet_table.setItem(row, 6, item6)

            item7_button = OperateButton("media/icons/chart.png", "media/icons/chart_hover.png", self)
            setattr(item7_button, "row_index", row)
            item7_button.clicked.connect(self.show_sheet_charts_values)
            self.variety_sheet_widget.sheet_table.setCellWidget(row, 7, item7_button)

            if row > 0:
                item8_button = OperateButton("media/icons/swap.png", "media/icons/swap_hover.png", self)
                setattr(item8_button, "row_index", row)
                item8_button.clicked.connect(self.sheet_to_top_show)
                self.variety_sheet_widget.sheet_table.setCellWidget(row, 8, item8_button)

            item9_button = OperateButton("media/icons/delete.png", "media/icons/delete_hover.png", self)
            setattr(item9_button, "row_index", row)
            item9_button.clicked.connect(self.delete_sheet_table)
            self.variety_sheet_widget.sheet_table.setCellWidget(row, 9, item9_button)

            check, text = (Qt.Checked, "自己") if row_item["is_private"] else (Qt.Unchecked, "公开")
            item10 = QTableWidgetItem(text)
            item10.setCheckState(check)
            self.variety_sheet_widget.sheet_table.setItem(row, 10, item10)
        # 还原表格单元格内容发生变化的信号
        self.variety_sheet_widget.sheet_table.cellChanged.connect(self.sheet_table_cell_changed)

    def delete_sheet_table(self):
        """ 删除数据表 """
        sender_button = self.sender()
        current_row = getattr(sender_button, "row_index")
        sheet_id = self.variety_sheet_widget.sheet_table.item(current_row, 0).text()
        warning = WarningPopup("确定删除这张数据表吗?删除后与其相关的图形等相关信息也将删除!", self)
        warning.set_data({"sheet_id": sheet_id})
        warning.confirm_operate.connect(self.confirm_delete_sheet)
        warning.exec_()

    def confirm_delete_sheet(self, data):
        """ 确定删除数据表 """
        sheet_id = data["sheet_id"]
        url = SERVER_API + "sheet/{}/".format(sheet_id)
        request = QNetworkRequest(QUrl(url))
        user_token = get_user_token()
        request.setRawHeader("Authorization".encode('utf-8'), user_token.encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.deleteResource(request)
        reply.finished.connect(self.delete_sheet_reply)

    def delete_sheet_reply(self):
        """ 删除数据表请求信号返回 """
        reply = self.sender()
        if reply.error():
            m = "删除表失败了{}".format(reply.error)
        else:
            m = "删除成功!"
        p = InformationPopup(m, self)
        p.exec_()
        # 重新获取数据
        self.get_show_variety_sheets()
        reply.deleteLater()

    def popup_option_chart(self, row, col):
        """ 品种表界面双击表名称进入绘图 """
        sheet_id = int(self.variety_sheet_widget.sheet_table.item(row, 0).text())
        sheet_name = self.variety_sheet_widget.sheet_table.item(row, 3).text()
        if col == 3:  # 双击sheet_name才能进入
            variety_en = self.variety_sheet_widget.variety_combobox.currentData()
            dispose_popup = DisposeChartPopup(variety_en, sheet_id, self)
            dispose_popup.setWindowTitle(sheet_name)
            dispose_popup.exec_()

    def sheet_table_cell_changed(self, row, col):
        """ 数据表的内容发生了变化 """
        # 关闭信号防止文字改变也发送一次信号
        self.variety_sheet_widget.sheet_table.cellChanged.disconnect()
        if col == 10:  # 发起修改私有化数据表的请求
            sheet_id = self.variety_sheet_widget.sheet_table.item(row, 0).text()
            is_private = 1 if self.variety_sheet_widget.sheet_table.item(row, col).checkState() else 0
            text = "自己" if is_private else "公开"
            self.variety_sheet_widget.sheet_table.item(row, col).setText(text)
            self.request_sheet_private(sheet_id, is_private)
        # 再次恢复信号
        self.variety_sheet_widget.sheet_table.cellChanged.connect(self.sheet_table_cell_changed)

    def request_sheet_private(self, sheet_id, is_private):
        """ 发请求sheet表私有化状态的改变 """
        url = SERVER_API + "sheet/{}/public/".format(sheet_id)
        user_token = get_user_token()
        network_manager = getattr(qApp, "_network")
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode('utf-8'), user_token.encode("utf-8"))
        reply = network_manager.post(request, json.dumps({"is_private": is_private}).encode("utf-8"))
        reply.finished.connect(self.modify_sheet_private_reply)

    def modify_sheet_private_reply(self):
        """ 修改sheet表返回 """
        reply = self.sender()
        reply.deleteLater()

    def show_sheet_charts_values(self):
        """ 弹窗显示表的图形和数据 """
        row_index = getattr(self.sender(), "row_index")
        sheet_id = self.variety_sheet_widget.sheet_table.item(row_index, 0).text()
        sheet_name = self.variety_sheet_widget.sheet_table.item(row_index, 3).text()
        is_own = 1 if self.variety_sheet_widget.only_me_check.checkState() else 0
        popup = SheetChartsPopup(sheet_id, is_own, self)
        popup.setWindowTitle(sheet_name)
        popup.exec_()

    def sheet_to_top_show(self):
        """ 将数据记录置顶 """
        # 取得上行的数据id和当前行的数据id
        row_index = getattr(self.sender(), "row_index")
        swap_id = self.variety_sheet_widget.sheet_table.item(row_index, 0).text()
        to_swap = self.variety_sheet_widget.sheet_table.item(row_index - 1, 0).text()
        body_data = {
            "swap_id": swap_id,
            "to_swap": to_swap,
            "swap_row": row_index
        }
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "sheet/suffix-swap/"
        reply = network_manager.put(QNetworkRequest(QUrl(url)), json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.swap_suffix_reply)

    def swap_suffix_reply(self):
        """ 交换后缀返回(指定) """
        reply = self.sender()
        if reply.error():
            logger.error("用户上移数据表错误:{}".format(reply.error()))
            return
        else:  # 取出当前行数据,并且移除,在首行插入
            # 从后端返回的数据取得行
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            current_row = data["swap_row"]
            # 交换上下行的值
            up_row = current_row - 1
            self.swap_variety_sheet_table_row(current_row, up_row)
        reply.deleteLater()

    def swap_variety_sheet_table_row(self, current_row, up_row):
        """ 数据表交换行数据行 """
        for col_index in range(7):
            current_item = self.variety_sheet_widget.sheet_table.item(current_row, col_index)
            up_row_item = self.variety_sheet_widget.sheet_table.item(up_row, col_index)
            current_text, up_text = current_item.text(), up_row_item.text()
            current_item.setText(up_text)
            up_row_item.setText(current_text)
            if col_index == 6:
                if int(up_text) > 0:
                    current_item.setForeground(QBrush(QColor(233,66,66)))
                else:
                    current_item.setForeground(QBrush(QColor(0, 0, 0)))
                if int(current_text) > 0:
                    up_row_item.setForeground(QBrush(QColor(233,66,66)))
                else:
                    up_row_item.setForeground(QBrush(QColor(0, 0, 0)))

    def chart_page_variety_changed(self):
        """ 图形显示页品种变化 """
        current_variety = self.sheet_chart_widget.variety_combobox.currentData()
        is_own = 1 if self.sheet_chart_widget.only_me_check.checkState() else 0
        user_token = get_user_token().split(" ")[1]
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "variety/{}/chart/?is_own={}&token={}".format(current_variety, is_own, user_token)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.variety_charts_reply)

    def variety_charts_reply(self):
        """ 品种的数据图形返回 """
        reply = self.sender()
        if reply.error():
            logger.error("用户获取品种的数据图形信息失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            self.show_variety_charts(data["data"])
        reply.deleteLater()

    def show_variety_charts(self, charts_list):
        """ 显示所有已配置的品种表 """
        self.sheet_chart_widget.chart_table.cellChanged.disconnect()  # 关闭单元格变化的信号
        self.sheet_chart_widget.chart_table.clear()

        if self.sheet_chart_widget.only_me_check.checkState():
            self.sheet_chart_widget.chart_table.setColumnCount(11)
            self.sheet_chart_widget.chart_table.setHorizontalHeaderLabels([
                "编号", "创建者", "创建日期", "标题", "解读", '图形', '上移', '主页', '品种', '删除', '可见'
            ])
        else:
            self.sheet_chart_widget.chart_table.setColumnCount(10)
            self.sheet_chart_widget.chart_table.setHorizontalHeaderLabels([
                "编号", "创建者", "创建日期", "标题", "解读", '图形', '上移', '主页', '品种', '删除'
            ])

        self.sheet_chart_widget.chart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.sheet_chart_widget.chart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.sheet_chart_widget.chart_table.setRowCount(len(charts_list))
        for row, row_item in enumerate(charts_list):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            self.sheet_chart_widget.chart_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["creator"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.sheet_chart_widget.chart_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["create_time"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.sheet_chart_widget.chart_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["title"])
            item3.setTextAlignment(Qt.AlignCenter)
            self.sheet_chart_widget.chart_table.setItem(row, 3, item3)

            item4_button = OperateButton("media/icons/edit.png", "media/icons/edit_hover.png", self.sheet_chart_widget.chart_table)
            setattr(item4_button, "row_index", row)
            item4_button.clicked.connect(self.edit_chart_decipherment)
            self.sheet_chart_widget.chart_table.setCellWidget(row, 4, item4_button)
            # 图形
            item5_button = OperateButton("media/icons/chart.png", "media/icons/chart_hover.png", self.sheet_chart_widget.chart_table)
            setattr(item5_button, "row_index", row)
            item5_button.clicked.connect(self.show_current_chart)
            self.sheet_chart_widget.chart_table.setCellWidget(row, 5, item5_button)
            # 上移
            if row > 0:
                item6_button = OperateButton("media/icons/swap.png", "media/icons/swap_hover.png", self.sheet_chart_widget.chart_table)
                setattr(item6_button, "row_index", row)
                item6_button.clicked.connect(self.swap_chart_suffix)
                self.sheet_chart_widget.chart_table.setCellWidget(row, 6, item6_button)

            # 主页
            item7 = QTableWidgetItem()
            if row_item["is_principal"] == "0":
                text = "隐藏"
                checked = Qt.Unchecked
            elif row_item["is_principal"] == "1":
                text = "审核"
                checked = Qt.PartiallyChecked
            else:
                text = "开启"
                checked = Qt.Checked
            item7.setText(text)
            item7.setCheckState(checked)
            self.sheet_chart_widget.chart_table.setItem(row, 7, item7)
            # 品种页
            item8 = QTableWidgetItem()
            checked, text = (Qt.Checked, "开启") if row_item["is_petit"] else (Qt.Unchecked, "隐藏")
            item8.setText(text)
            item8.setCheckState(checked)
            self.sheet_chart_widget.chart_table.setItem(row, 8, item8)
            # 删除
            item9_button = OperateButton("media/icons/delete.png", "media/icons/delete_hover.png", self)
            setattr(item9_button, "row_index", row)
            item9_button.clicked.connect(self.user_delete_chart)
            self.sheet_chart_widget.chart_table.setCellWidget(row, 9, item9_button)

            # 仅自己可见
            item10 = QTableWidgetItem()
            checked, text = (Qt.Checked, "自己") if row_item["is_private"] else (Qt.Unchecked, "公开")
            item10.setCheckState(checked)
            item10.setText(text)
            self.sheet_chart_widget.chart_table.setItem(row, 10, item10)

        # 重新连接单元格变化的信号
        self.sheet_chart_widget.chart_table.cellChanged.connect(self.chart_table_cell_changed)  # 图形表单元格变化

    def user_delete_chart(self):
        """ 用户删除图形"""
        sender_button = self.sender()
        current_row = getattr(sender_button, "row_index")
        chart_id = self.sheet_chart_widget.chart_table.item(current_row, 0).text()
        warning = WarningPopup("确定删除这张图形吗?删除后将不可恢复!", self)
        warning.set_data({"chart_id": chart_id})
        warning.confirm_operate.connect(self.confirm_delete_chart)
        warning.exec_()

    def confirm_delete_chart(self, data):
        """ 确定删除数据图形 """
        chart_id = data["chart_id"]
        url = SERVER_API + "chart/{}/".format(chart_id)
        request = QNetworkRequest(QUrl(url))
        user_token = get_user_token()
        request.setRawHeader("Authorization".encode('utf-8'), user_token.encode("utf-8"))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.deleteResource(request)
        reply.finished.connect(self.delete_chart_reply)

    def delete_chart_reply(self):
        """ 删除图形返回 """
        reply = self.sender()
        if reply.error():
            m = "删除图形失败了{}".format(reply.error)
        else:
            m = "删除成功!"
        p = InformationPopup(m, self)
        p.exec_()
        self.chart_page_variety_changed()  # 重新加载图形

    def edit_chart_decipherment(self):
        """ 编辑当前图形的解说 """
        current_row = getattr(self.sender(), "row_index")
        chart_id = self.sheet_chart_widget.chart_table.item(current_row, 0).text()
        popup = DeciphermentPopup(chart_id, self)
        popup.show()

    def show_current_chart(self):
        """ 显示当前的图形 """
        current_row = getattr(self.sender(), "row_index")
        chart_id = self.sheet_chart_widget.chart_table.item(current_row, 0).text()
        chart_name = self.sheet_chart_widget.chart_table.item(current_row, 3).text()
        popup = ChartPopup(chart_id, self)
        popup.setWindowTitle(chart_name)
        popup.setWindowIcon(QIcon("media/icons/chart.png"))
        popup.show()

    def swap_chart_suffix(self):
        """ 交换上移行 """
        row_index = getattr(self.sender(), "row_index")
        swap_id = self.sheet_chart_widget.chart_table.item(row_index, 0).text()
        to_swap = self.sheet_chart_widget.chart_table.item(row_index - 1, 0).text()
        body_data = {
            "swap_id": swap_id,
            "to_swap": to_swap,
            "swap_row": row_index
        }
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "chart/suffix-swap/"
        reply = network_manager.put(QNetworkRequest(QUrl(url)), json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.swap_chart_suffix_reply)

    def swap_chart_suffix_reply(self):
        """ 交换数据图形后缀返回 """
        reply = self.sender()
        if reply.error():
            logger.error("用户上移图形错误:{}".format(reply.error()))
            return
        else:  # 取出当前行数据,并且移除,在首行插入
            # 从后端返回的数据取得行
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            current_row = data["swap_row"]
            # 交换上下行的值
            up_row = current_row - 1
            self.swap_variety_chart_table_row(current_row, up_row)
        reply.deleteLater()

    def swap_variety_chart_table_row(self, current_row, up_row):
        """ 图形表交换行数据行 """
        for col_index in range(4):
            current_item = self.sheet_chart_widget.chart_table.item(current_row, col_index)
            up_row_item = self.sheet_chart_widget.chart_table.item(up_row, col_index)
            current_text, up_text = current_item.text(), up_row_item.text()
            current_item.setText(up_text)
            up_row_item.setText(current_text)

    def load_variety_charts_render(self):
        """ 加载品种的所有图形 """
        user_token = get_user_token().split(' ')[1]
        is_own = 1 if self.sheet_chart_widget.only_me_check.checkState() else 0
        variety_en = self.sheet_chart_widget.variety_combobox.currentData()
        url = SERVER_API + "variety/{}/chart/?is_own={}&render=1&token={}".format(variety_en, is_own, user_token)
        self.sheet_chart_widget.chart_container.load(QUrl(url))

    def swap_to_render_variety_charts(self, tab_index):
        """ 切换渲染品种下的图形 """
        if tab_index == 1:
            self.load_variety_charts_render()

    def chart_table_cell_changed(self, row, col):
        """ 数据图形单元格变化 """
        # 断开信号(防止两列的变化都发送一次请求)
        self.sheet_chart_widget.chart_table.cellChanged.disconnect()  # 图形表单元格变化
        if col in [7, 8, 10]:
            chart_id = self.sheet_chart_widget.chart_table.item(row, 0).text()
            is_principal = self.sheet_chart_widget.chart_table.item(row, 7).checkState()
            is_petit = 1 if self.sheet_chart_widget.chart_table.item(row, 8).checkState() else 0
            is_private = 1 if self.sheet_chart_widget.chart_table.item(row, 10).checkState() else 0
            self.change_chart_display_position(chart_id, is_principal, is_petit, is_private)
            if is_principal == 1:
                text = "审核"
            elif is_principal == 2:
                text = "开启"
            else:
                text = "隐藏"
            self.sheet_chart_widget.chart_table.item(row, 7).setText(text)
            text = "开启" if is_petit else "隐藏"
            self.sheet_chart_widget.chart_table.item(row, 8).setText(text)
            text = "自己" if is_private else "公开"
            self.sheet_chart_widget.chart_table.item(row, 10).setText(text)
        # 再次链接信号
        self.sheet_chart_widget.chart_table.cellChanged.connect(self.chart_table_cell_changed)  # 图形表单元格变化

    def change_chart_display_position(self, chart_id, is_principal, is_petit, is_private):
        """ 修改图形的显示位置 """
        user_token = get_user_token()
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'chart/{}/display/?is_principal={}&is_petit={}&is_private={}'.format(chart_id, is_principal, is_petit, is_private)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.put(request, None)
        reply.finished.connect(self.change_chart_display_reply)

    def change_chart_display_reply(self):
        """ 设置图形的显示位置返回 """
        reply = self.sender()
        if reply.error():
            logger.error("用户修改图形显示失败:{}".format(reply.error()))
        else:
            p = InformationPopup("设置成功!", self)
            p.exec_()
        reply.deleteLater()
