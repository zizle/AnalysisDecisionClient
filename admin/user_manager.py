# _*_ coding:utf-8 _*_
# @File  : user_manager.py
# @Time  : 2020-09-01 15:31
# @Author: zizle
import json
from datetime import datetime
from PyQt5.QtWidgets import qApp, QTableWidgetItem, QPushButton, QComboBox
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QBrush, QColor
from settings import SERVER_API, logger, SYSTEM_MENUS
from utils.client import get_user_token
from .user_manager_ui import UserManagerUI, UserClientAuthUI, UserModuleAuthUI, UserVarietyAuthUI


class UserManager(UserManagerUI):
    """ 用户管理业务逻辑 """
    ROLE_ZH = {
        "superuser": "超级管理员",
        "operator": "运营管理员",
        "collector": "信息管理员",
        "research": "品种研究员",
        "normal": "客户端用户"
    }

    def __init__(self, *args, **kwargs):
        super(UserManager, self).__init__(*args, **kwargs)
        self.user_list_widget.query_button.clicked.connect(self._get_current_role_users)
        self.user_list_widget.show_user_table.cellChanged.connect(self.user_table_cell_changed)  # 用户表内容改变

        self._get_current_role_users()
        self.currentChanged.connect(self.current_tab_changed)  # tab返回用户列表信号

    def current_tab_changed(self, tab_index):
        """ 当前标签改变去除新增加出来的标签 """
        if tab_index == 0:
            tab_widget = self.widget(1)
            if isinstance(tab_widget, UserModuleAuthUI):
                print("模块验证移除")
                self.module_auth.current_user_id = None
                self.module_auth.module_auth_table.cellChanged.disconnect()  # 切断table的信号关系,否则报错
            if isinstance(tab_widget, UserClientAuthUI):
                print("客户端验证移除")
                self.client_auth.current_user_id = None
                self.client_auth.client_auth_table.cellChanged.disconnect()
            if isinstance(tab_widget, UserVarietyAuthUI):
                self.variety_auth.current_user_id = None
                self.variety_auth.variety_auth_table.cellChanged.disconnect()
            self.removeTab(1)

    def _get_current_role_users(self):
        """ 获取当前角色的用户 """
        self.user_list_widget.show_user_table.cellChanged.disconnect()

        current_role = self.user_list_widget.user_role_combobox.currentData()
        user_token = get_user_token()
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'all-users/?role={}'.format(current_role)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode('utf-8'))
        reply = network_manager.get(request)
        reply.finished.connect(self.get_users_reply)

    def get_users_reply(self):
        """ 获取用户返回了 """
        reply = self.sender()
        if reply.error():
            logger.error("获取用户列表失败:{}".format(reply.error()))
            reply.deleteLater()
            return
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()

        self.show_all_users(data["users"])

        self.user_list_widget.show_user_table.cellChanged.connect(self.user_table_cell_changed)

    def show_all_users(self, user_list):
        """ 显示所有的用户 """
        self.user_list_widget.show_user_table.clearContents()
        self.user_list_widget.show_user_table.setRowCount(len(user_list))
        for row, row_item in enumerate(user_list):
            item0 = QTableWidgetItem(str(row_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            self.user_list_widget.show_user_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(row_item["username"])
            item1.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(row_item["phone"])
            item2.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(row_item["user_code"])
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setFlags(Qt.ItemIsEditable)
            self.user_list_widget.show_user_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(row_item["email"])
            item4.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 4, item4)

            # item5 = QTableWidgetItem(self.ROLE_ZH.get(row_item["role"], "未知"))
            # item5.setTextAlignment(Qt.AlignCenter)
            # self.user_list_widget.show_user_table.setItem(row, 5, item5)

            item10 = QTableWidgetItem(str(row_item["note"]))
            item10.setTextAlignment(Qt.AlignCenter)
            self.user_list_widget.show_user_table.setItem(row, 10, item10)

            if row_item["role"] not in ["superuser"]:
                item5 = QComboBox(self)
                for role_en, role_cn in self.ROLE_ZH.items():
                    if role_en == "superuser":
                        continue
                    item5.addItem(role_cn, role_en)
                    item5.setCurrentText(self.ROLE_ZH.get(row_item["role"]))  # 设置当前
                self.user_list_widget.show_user_table.setCellWidget(row, 5, item5)

                item6 = QTableWidgetItem()

                state, text, fcolor = (Qt.Checked, '在职', QColor(0, 0, 0)) if row_item["is_active"] else (Qt.Unchecked, '离职', QColor(122, 210, 55))
                item6.setCheckState(state)
                item6.setText(text)
                item6.setTextAlignment(Qt.AlignCenter)
                item6.setForeground(QBrush(fcolor))
                self.user_list_widget.show_user_table.setItem(row, 6, item6)

                confirm_button = QPushButton("确定", self)
                setattr(confirm_button, "row_index", row)
                confirm_button.clicked.connect(self.modify_user_information)
                self.user_list_widget.show_user_table.setCellWidget(row, 11, confirm_button)

                login_button = QPushButton("编辑", self)   # 登录权限
                setattr(login_button, "row_index", row)
                login_button.clicked.connect(self.to_login_authority)
                self.user_list_widget.show_user_table.setCellWidget(row, 7, login_button)

                module_button = QPushButton("编辑", self)     # 模块权限
                setattr(module_button, "row_index", row)
                module_button.clicked.connect(self.to_module_authority)
                self.user_list_widget.show_user_table.setCellWidget(row, 8, module_button)

                variety_button = QPushButton("编辑", self)     # 品种权限
                setattr(variety_button, "row_index", row)
                variety_button.clicked.connect(self.to_variety_authority)
                self.user_list_widget.show_user_table.setCellWidget(row, 9, variety_button)

    def user_table_cell_changed(self, row, col):
        """ 用户显示表的内容改变 """
        if col == 6:
            item = self.user_list_widget.show_user_table.item(row, col)
            text, f_color = ("在职", QColor(0, 0, 0)) if item.checkState() else ("离职", QColor(122, 210, 55))
            item.setForeground(QBrush(f_color))
            item.setText(text)

    def modify_user_information(self):
        """ 修改用户的基础信息 """
        current_row = getattr(self.sender(), "row_index")
        role = self.user_list_widget.show_user_table.cellWidget(current_row, 5).currentData()
        is_active = 1 if self.user_list_widget.show_user_table.item(current_row, 6).checkState() else 0
        body_data = {
            "modify_id": self.user_list_widget.show_user_table.item(current_row, 0).text(),
            "user_code": self.user_list_widget.show_user_table.item(current_row, 3).text(),
            "username": self.user_list_widget.show_user_table.item(current_row, 1).text(),
            "phone": self.user_list_widget.show_user_table.item(current_row, 2).text(),
            "email": self.user_list_widget.show_user_table.item(current_row, 4).text(),
            "role": role,
            "is_active": is_active,
            "note": self.user_list_widget.show_user_table.item(current_row, 10).text()
        }
        user_token = get_user_token()
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "user/info/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode('utf-8'))
        reply = network_manager.put(request, json.dumps(body_data).encode('utf-8'))
        reply.finished.connect(self.modify_information_reply)

    def modify_information_reply(self):
        """ 修改用户基本信息返回 """
        reply = self.sender()
        data = reply.readAll().data()
        print(data)
        data = json.loads(data.decode("utf-8"))
        print(data)
        if reply.error():
            self.user_list_widget.network_message.setText(str(data["detail"]))
        else:
            self.user_list_widget.network_message.setText(data["message"])
        reply.deleteLater()

    """ 登录权限管理 """

    def to_login_authority(self):
        """ 跳转登录权限管理页面 """
        current_row = getattr(self.sender(), "row_index")
        if current_row is None:
            return
        current_user_id = self.user_list_widget.show_user_table.item(current_row, 0).text()

        # 请求当前用户的客户端登录权限情况
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "user/client-authenticate/?query_user=" + str(current_user_id)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_client_authority_reply)

        tab_index = self.addTab(self.client_auth, "登录权限")
        self.setCurrentIndex(tab_index)

    def user_client_authority_reply(self):
        """ 请求用户客户端权限返回 """
        reply = self.sender()
        if reply.error():
            self.module_auth.network_message.setText("数据请求失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            current_user_info = data.get("user")
            if current_user_info:
                self.client_auth.current_user_id = current_user_info["id"]  # 绑定当前用户的ID到界面
                self.client_auth.current_username.setText(current_user_info["username"])
                self.client_auth.current_user_code.setText(current_user_info["user_code"])
                self.client_auth.network_message.setText("")
            else:                                                           # 操作用户登录过期了
                self.client_auth.current_user_id = None
                self.client_auth.current_username.setText("")
                self.client_auth.current_user_code.setText("")
                self.client_auth.network_message.setText("登录信息已过期,重新登录后再操作!")
                self.parent().parent().user_logout(to_homepage=False)       # 退出navigationBar的用户名显示
            self.client_auth_show_clients(data["clients"])
            self.client_auth.client_auth_table.cellChanged.connect(self.client_auth_status)  # 连接开启和关闭改变的信号
        reply.deleteLater()

    def client_auth_show_clients(self, auth_clients):
        """ 客户端权限页面显示所有客户端 """
        self.client_auth.client_auth_table.clearContents()
        self.client_auth.client_auth_table.setRowCount(len(auth_clients))
        for row, client_item in enumerate(auth_clients):
            item0 = QTableWidgetItem(str(client_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            item0.setForeground(QBrush(QColor(0, 0, 0)))
            self.client_auth.client_auth_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(client_item["client_name"])
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(Qt.ItemIsEditable)
            item1.setForeground(QBrush(QColor(0, 0, 0)))
            self.client_auth.client_auth_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(client_item["machine_uuid"])
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setFlags(Qt.ItemIsEditable)
            item2.setForeground(QBrush(QColor(0, 0, 0)))
            self.client_auth.client_auth_table.setItem(row, 2, item2)

            checked, expire_date = self.is_client_opened(client_item["expire_date"])
            text = "允许登录" if checked else "拒绝登录"
            item3 = QTableWidgetItem(text)
            item3.setCheckState(checked)
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setForeground(QBrush(QColor(128, 195, 66))) if checked else item3.setForeground(QBrush(QColor(233, 66, 66)))
            self.client_auth.client_auth_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(expire_date)
            item4.setTextAlignment(Qt.AlignCenter)
            self.client_auth.client_auth_table.setItem(row, 4, item4)

            item5_widget = QPushButton("确定", self.client_auth.client_auth_table)
            setattr(item5_widget, "row_index", row)
            item5_widget.clicked.connect(self.confirm_user_client_authority)
            self.client_auth.client_auth_table.setCellWidget(row, 5, item5_widget)

    @staticmethod
    def is_client_opened(expire_date):
        """ 验证是否有登录权限 """
        today_str = datetime.today().strftime("%Y-%m-%d")
        is_opened = Qt.Unchecked
        if expire_date:
            if expire_date > today_str:
                is_opened = Qt.Checked
        else:
            expire_date = "2020-01-01"
        return is_opened, expire_date

    def client_auth_status(self, row, col):
        """ 客户端权限开启和关闭状态改变 """
        if col == 3:
            checked_item = self.client_auth.client_auth_table.item(row, col)
            expire_date_item = self.client_auth.client_auth_table.item(row, col + 1)
            if checked_item.checkState():
                checked_item.setText("允许登录")
                checked_item.setForeground(QBrush(QColor(128, 195, 66)))
                if expire_date_item.text() < datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("3000-01-01")

            if not checked_item.checkState():
                checked_item.setText("拒绝登录")
                checked_item.setForeground(QBrush(QColor(233, 66, 66)))
                if expire_date_item.text() > datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("2020-01-01")
        if col == 4:
            expire_date_item = self.client_auth.client_auth_table.item(row, 4)
            try:
                datetime.strptime(expire_date_item.text(), "%Y-%m-%d")
            except Exception:
                # self.module_auth.network_message.setText("有效期格式为yyyy-mm-dd !")
                expire_date_item.setText("2020-01-01")

    def confirm_user_client_authority(self):
        """ 确定修改用户客户端登录权限 """
        current_row = getattr(self.sender(), "row_index")
        client_id = self.client_auth.client_auth_table.item(current_row, 0).text()
        expire_date = self.client_auth.client_auth_table.item(current_row, 4).text()
        body_data = {
            "modify_user": self.client_auth.current_user_id,
            "client_id": client_id,
            "expire_date": expire_date
        }
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/client-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.put(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.modify_client_authority_reply)

    def modify_client_authority_reply(self):
        """ 修改用户客户端登录权限返回 """
        reply = self.sender()
        data = reply.readAll().data()

        if reply.error():
            self.client_auth.network_message.setText("修改失败了:{}".format(reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.client_auth.network_message.setText(data["message"])
        reply.deleteLater()

    """ 模块权限管理 """

    def to_module_authority(self):
        """ 跳转模块权限页面 """
        current_row = getattr(self.sender(), "row_index")
        if current_row is None:
            return
        current_user_id = self.user_list_widget.show_user_table.item(current_row, 0).text()

        # 请求当前用户的模块权限情况
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "user/module-authenticate/?query_user=" + str(current_user_id)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_module_authority_reply)
        tab_index = self.addTab(self.module_auth, "模块权限")
        self.setCurrentIndex(tab_index)

    def user_module_authority_reply(self):
        """ 获取用户模块权限返回 """
        reply = self.sender()
        if reply.error():
            self.module_auth.network_message.setText("数据请求失败:{}".format(reply.error()))
            reply.deleteLater()
            return
        self.module_auth.network_message.setText("")
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()
        current_user_info = data.get("user")
        if current_user_info:
            self.module_auth.current_user_id = current_user_info["id"]                      # 绑定当前用户的ID到界面
            self.module_auth.current_username.setText(current_user_info["username"])
            self.module_auth.current_user_code.setText(current_user_info["user_code"])
            self.module_auth.network_message.setText('')
            current_user_role = current_user_info["role"]
        else:
            self.module_auth.current_user_id = None
            self.module_auth.current_username.setText('')
            self.module_auth.current_user_code.setText('')
            self.module_auth.network_message.setText('登录信息已过期,重新登录后再操作!')
            self.parent().parent().user_logout(to_homepage=False)
            current_user_role = None

        # 将后端返回的模块转为module_id为KEY,expire_date为VALUE的字典
        auth_modules = {module_item["module_id"]: module_item["expire_date"] for module_item in data["modules"]}
        self.module_auth_show_modules(current_user_role, auth_modules)

        self.module_auth.module_auth_table.cellChanged.connect(self.module_auth_status)  # 连接开启和关闭改变的信号

    def module_auth_show_modules(self, user_role, auth_modules):
        """ 在模块管理页面显示所有功能模块 """
        self.module_auth.module_auth_table.clearContents()
        self.module_auth.module_auth_table.setRowCount(0)
        if user_role is None:   # 操作用户登录过期,不再往下执行
            return
        for module_item in SYSTEM_MENUS:
            if user_role == "research" and module_item["id"] >= "0":
                continue
            row = self.module_auth.module_auth_table.rowCount()
            self.module_auth.module_auth_table.insertRow(row)
            item0 = QTableWidgetItem(module_item["id"])
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            item0.setBackground(QBrush(QColor(122, 210, 55)))
            item0.setForeground(QBrush(QColor(0, 0, 0)))
            self.module_auth.module_auth_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(module_item["name"])
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(Qt.ItemIsEditable)
            item1.setBackground(QBrush(QColor(122, 210, 55)))
            item1.setForeground(QBrush(QColor(0, 0, 0)))
            self.module_auth.module_auth_table.setItem(row, 1, item1)

            self._set_module_auth_blank_items(row, QColor(122, 210, 55))

            if module_item["children"]:
                for module_c_1 in module_item["children"]:
                    row = self.module_auth.module_auth_table.rowCount()
                    self.module_auth.module_auth_table.insertRow(row)

                    item0 = QTableWidgetItem(module_c_1["id"])
                    item0.setTextAlignment(Qt.AlignCenter)
                    item0.setFlags(Qt.ItemIsEditable)
                    item0.setForeground(QBrush(QColor(122, 210, 55)))
                    self.module_auth.module_auth_table.setItem(row, 0, item0)

                    item1 = QTableWidgetItem(module_c_1["name"])
                    item1.setTextAlignment(Qt.AlignCenter)
                    item1.setFlags(Qt.ItemIsEditable)
                    item1.setForeground(QBrush(QColor(122, 210, 55)))

                    self.module_auth.module_auth_table.setItem(row, 1, item1)

                    self._set_module_auth_blank_items(row)

                    if module_c_1["children"]:
                        for module_c_2 in module_c_1["children"]:
                            row = self.module_auth.module_auth_table.rowCount()
                            self.module_auth.module_auth_table.insertRow(row)

                            item0 = QTableWidgetItem(module_c_2["id"])
                            item0.setTextAlignment(Qt.AlignCenter)
                            item0.setFlags(Qt.ItemIsEditable)
                            item0.setForeground(QBrush(QColor(48, 169, 249)))
                            self.module_auth.module_auth_table.setItem(row, 0, item0)

                            item1 = QTableWidgetItem(module_c_2["name"])
                            item1.setTextAlignment(Qt.AlignCenter)
                            item1.setFlags(Qt.ItemIsEditable)
                            item1.setForeground(QBrush(QColor(48, 169, 249)))
                            self.module_auth.module_auth_table.setItem(row, 1, item1)

                            checked, expire_date = self.is_module_authenticated(user_role, module_c_2["id"], auth_modules)
                            self._set_module_auth_options_items(row, checked, expire_date, QColor(48, 169, 249))

                    else:
                        checked, expire_date = self.is_module_authenticated(user_role, module_c_1["id"], auth_modules)
                        self._set_module_auth_options_items(row, checked, expire_date, QColor(122, 210, 55))

            else:
                checked, expire_date = self.is_module_authenticated(user_role, module_item["id"], auth_modules)
                self._set_module_auth_options_items(row, checked, expire_date, QColor(122, 210, 55), QColor(122, 210, 55))

    @staticmethod
    def is_module_authenticated(user_role, module_id, auth_modules):
        """ 验证模块是否有权限
            module_id：待验证的模块id
            auth_modules：后端返回的转为字典的权限模块
        """
        today_str = datetime.today().strftime("%Y-%m-%d")
        expire_date = auth_modules.get(module_id)
        if user_role in ["superuser", "operator"]:
            expire_date = "3000-01-01"
        is_authenticated = Qt.Unchecked
        if expire_date:
            if expire_date > today_str:
                is_authenticated = Qt.Checked
        else:
            expire_date = "2020-01-01"
        return is_authenticated, expire_date

    def _set_module_auth_blank_items(self, row, q_color=None):
        """ 设置空的item """
        item2 = QTableWidgetItem()
        item2.setFlags(Qt.ItemIsEditable)
        if q_color:
            item2.setBackground(QBrush(q_color))
        self.module_auth.module_auth_table.setItem(row, 2, item2)

        item3 = QTableWidgetItem()
        item3.setFlags(Qt.ItemIsEditable)
        if q_color:
            item3.setBackground(QBrush(q_color))
        self.module_auth.module_auth_table.setItem(row, 3, item3)

        item4 = QTableWidgetItem()
        item4.setFlags(Qt.ItemIsEditable)
        if q_color:
            item4.setBackground(QBrush(q_color))
        self.module_auth.module_auth_table.setItem(row, 4, item4)

    def _set_module_auth_options_items(self, row, checked, expire_date, f_color, b_color=None):
        """ 设置模块管理的操作项目(选择开启或关闭,设置到期时间等) """
        text = "开放" if checked else "关闭"
        item2 = QTableWidgetItem(text)
        item2.setCheckState(checked)
        item2.setTextAlignment(Qt.AlignCenter)
        item2.setBackground(QBrush(b_color)) if b_color else item2.setForeground(QBrush(f_color))
        self.module_auth.module_auth_table.setItem(row, 2, item2)

        item3 = QTableWidgetItem(expire_date)
        item3.setBackground(QBrush(b_color)) if b_color else item3.setForeground(QBrush(f_color))
        item3.setTextAlignment(Qt.AlignCenter)
        self.module_auth.module_auth_table.setItem(row, 3, item3)

        item4_widget = QPushButton("确定", self.module_auth.module_auth_table)
        item4_widget.clicked.connect(self.edit_user_module_authority)
        setattr(item4_widget, "row_index", row)
        self.module_auth.module_auth_table.setCellWidget(row, 4, item4_widget)

    def module_auth_status(self, row, col):
        """ 模块权限开启和关闭变化的信号 """
        if col == 2:
            checked_item = self.module_auth.module_auth_table.item(row, col)
            expire_date_item = self.module_auth.module_auth_table.item(row, col + 1)
            if checked_item.checkState():
                checked_item.setText("开启")
                if expire_date_item.text() < datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("3000-01-01")

            if not checked_item.checkState():
                checked_item.setText("关闭")
                if expire_date_item.text() > datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("2020-01-01")
        if col == 3:
            expire_date_item = self.module_auth.module_auth_table.item(row, 3)
            try:
                datetime.strptime(expire_date_item.text(), "%Y-%m-%d")
            except Exception:
                # self.module_auth.network_message.setText("有效期格式为yyyy-mm-dd !")
                expire_date_item.setText("2020-01-01")

    def edit_user_module_authority(self):
        """ 编辑用户权限 """
        row_index = getattr(self.sender(), "row_index")
        module_id = self.module_auth.module_auth_table.item(row_index, 0).text()
        module_text = self.module_auth.module_auth_table.item(row_index, 1).text()
        expire_date = self.module_auth.module_auth_table.item(row_index, 3).text()
        body_data = {
            "modify_user": self.module_auth.current_user_id,
            "module_id": module_id,
            "module_text": module_text,
            "expire_date": expire_date
        }
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/module-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.put(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.modify_module_authority_reply)

    def modify_module_authority_reply(self):
        """ 修改模块权限返回 """
        reply = self.sender()
        data = reply.readAll().data()

        if reply.error():
            self.module_auth.network_message.setText("修改失败了:{}".format(reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.module_auth.network_message.setText(data["message"])
        reply.deleteLater()

    """ 品种权限管理 """

    def to_variety_authority(self):
        """ 跳转品种权限页面 """
        current_row = getattr(self.sender(), "row_index")
        if current_row is None:
            return
        current_user_id = self.user_list_widget.show_user_table.item(current_row, 0).text()

        # 请求当前用户的客户端登录权限情况
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "user/variety-authenticate/?query_user=" + str(current_user_id)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.get(request)
        reply.finished.connect(self.user_variety_authority_reply)

        tab_index = self.addTab(self.variety_auth, "品种权限")
        self.setCurrentIndex(tab_index)

    def user_variety_authority_reply(self):
        """ 请求用户品种权限返回 """
        reply = self.sender()
        if reply.error():
            self.variety_auth.network_message.setText("数据请求失败:{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode("utf-8"))
            current_user_info = data.get('user')
            if current_user_info:
                self.variety_auth.current_user_id = current_user_info["id"]  # 绑定当前用户的ID到界面
                self.variety_auth.current_username.setText(current_user_info["username"])
                self.variety_auth.current_user_code.setText(current_user_info["user_code"])
                self.variety_auth.network_message.setText('')
            else:
                self.variety_auth.current_user_id = None
                self.variety_auth.current_username.setText("")
                self.variety_auth.current_user_code.setText("")
                self.variety_auth.network_message.setText("登录信息已过期,重新登录后再操作!")
                self.parent().parent().user_logout(to_homepage=False)

            self.variety_auth_show_varieties(data["varieties"])
            self.variety_auth.variety_auth_table.cellChanged.connect(self.variety_auth_status)  # 连接开启和关闭改变的信号
        reply.deleteLater()

    def variety_auth_show_varieties(self, variety_list):
        """ 显示当前用户品种权限情况 """
        self.variety_auth.variety_auth_table.clearContents()
        self.variety_auth.variety_auth_table.setRowCount(len(variety_list))
        for row, client_item in enumerate(variety_list):
            item0 = QTableWidgetItem(str(client_item["id"]))
            item0.setTextAlignment(Qt.AlignCenter)
            item0.setFlags(Qt.ItemIsEditable)
            item0.setForeground(QBrush(QColor(0, 0, 0)))
            self.variety_auth.variety_auth_table.setItem(row, 0, item0)

            item1 = QTableWidgetItem(client_item["variety_name"])
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(Qt.ItemIsEditable)
            item1.setForeground(QBrush(QColor(0, 0, 0)))
            self.variety_auth.variety_auth_table.setItem(row, 1, item1)

            item2 = QTableWidgetItem(client_item["variety_en"])
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setFlags(Qt.ItemIsEditable)
            item2.setForeground(QBrush(QColor(0, 0, 0)))
            self.variety_auth.variety_auth_table.setItem(row, 2, item2)

            item3 = QTableWidgetItem(client_item["exchange_lib"])
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setFlags(Qt.ItemIsEditable)
            item3.setForeground(QBrush(QColor(0, 0, 0)))
            self.variety_auth.variety_auth_table.setItem(row, 3, item3)

            item4 = QTableWidgetItem(client_item["group_name"])
            item4.setTextAlignment(Qt.AlignCenter)
            item4.setFlags(Qt.ItemIsEditable)
            item4.setForeground(QBrush(QColor(0, 0, 0)))
            self.variety_auth.variety_auth_table.setItem(row, 4, item4)

            checked, expire_date = self.is_variety_opened(client_item["expire_date"])
            text = "开放" if checked else "关闭"
            item5 = QTableWidgetItem(text)
            item5.setCheckState(checked)
            item5.setTextAlignment(Qt.AlignCenter)
            item5.setForeground(QBrush(QColor(128, 195, 66))) if checked else item5.setForeground(QBrush(QColor(233, 66, 66)))
            self.variety_auth.variety_auth_table.setItem(row, 5, item5)

            item6 = QTableWidgetItem(expire_date)
            item6.setTextAlignment(Qt.AlignCenter)
            self.variety_auth.variety_auth_table.setItem(row, 6, item6)

            item7_widget = QPushButton("确定", self.client_auth.client_auth_table)
            setattr(item7_widget, "row_index", row)
            item7_widget.clicked.connect(self.confirm_user_variety_authority)
            self.variety_auth.variety_auth_table.setCellWidget(row, 7, item7_widget)

    @staticmethod
    def is_variety_opened(expire_date):
        """ 验证是否有登录权限 """
        today_str = datetime.today().strftime("%Y-%m-%d")
        is_opened = Qt.Unchecked
        if expire_date:
            if expire_date > today_str:
                is_opened = Qt.Checked
        else:
            expire_date = "2020-01-01"
        return is_opened, expire_date

    def variety_auth_status(self, row, col):
        """ 开启和关闭品种权限的信号 """
        if col == 5:
            checked_item = self.variety_auth.variety_auth_table.item(row, col)
            expire_date_item = self.variety_auth.variety_auth_table.item(row, col + 1)
            if checked_item.checkState():
                checked_item.setText("开放")
                checked_item.setForeground(QBrush(QColor(128, 195, 66)))
                if expire_date_item.text() < datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("3000-01-01")

            if not checked_item.checkState():
                checked_item.setText("关闭")
                checked_item.setForeground(QBrush(QColor(233, 66, 66)))
                if expire_date_item.text() > datetime.today().strftime("%Y-%m-%d"):
                    expire_date_item.setText("2020-01-01")
        if col == 6:
            expire_date_item = self.variety_auth.variety_auth_table.item(row, 6)
            try:
                datetime.strptime(expire_date_item.text(), "%Y-%m-%d")
            except Exception:
                # self.module_auth.network_message.setText("有效期格式为yyyy-mm-dd !")
                expire_date_item.setText("2020-01-01")

    def confirm_user_variety_authority(self):
        """ 确定修改用户的品种权限 """
        current_row = getattr(self.sender(), "row_index")
        variety_id = self.variety_auth.variety_auth_table.item(current_row, 0).text()
        variety_en = self.variety_auth.variety_auth_table.item(current_row, 2).text()
        expire_date = self.variety_auth.variety_auth_table.item(current_row, 6).text()
        body_data = {
            "modify_user": self.variety_auth.current_user_id,
            "variety_id": variety_id,
            "variety_en": variety_en,
            "expire_date": expire_date
        }
        network_manager = getattr(qApp, "_network")
        user_token = get_user_token()
        url = SERVER_API + "user/variety-authenticate/"
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.put(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.modify_variety_authority_reply)

    def modify_variety_authority_reply(self):
        """ 修改用户品种权限返回 """
        reply = self.sender()
        data = reply.readAll().data()
        print(data)
        if reply.error():
            self.variety_auth.network_message.setText("修改失败了:{}".format(reply.error()))
        else:
            data = json.loads(data.decode("utf-8"))
            self.variety_auth.network_message.setText(data["message"])
        reply.deleteLater()
