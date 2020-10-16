# _*_ coding:utf-8 _*_
# @File  : short_message.py
# @Time  : 2020-09-18 15:56
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QMargins, Qt, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from utils.client import get_user_token
from settings import SERVER_API, logger
from popup.message import InformationPopup, WarningPopup
from .short_message_ui import ShortMessageAdminUI, ModifyMessagePopup


class ContentSignalLabel(QWidget):
    def __init__(self, content, msg_id,  *args, **kwargs):
        super(ContentSignalLabel, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.msg_id = msg_id
        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        opt_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        opt_layout.addStretch()

        modify_button = QPushButton("修改", self)
        modify_button.clicked.connect(self.modify_short_message)
        opt_layout.addWidget(modify_button)

        delete_button = QPushButton("删除", self)
        delete_button.clicked.connect(self.delete_short_message)
        opt_layout.addWidget(delete_button)

        self.content_label = QLabel(content, self)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(self.content_label)
        main_layout.addLayout(opt_layout)
        self.setLayout(main_layout)

    def modify_short_message(self):
        """ 修改一条短信通的内容 """
        # 弹窗修改
        edit_popup = ModifyMessagePopup(self)
        text = self.content_label.text()
        edit_popup.text_edit.setText(text)
        edit_popup.request_modify.connect(self.confirm_modify_message)
        edit_popup.exec_()

    def confirm_modify_message(self, content):
        """ 确定修改内容 """
        def modify_finished():
            f_reply = self.sender()
            if f_reply.error():
                p_info = InformationPopup("修改失败了!\n只能修改自己发送的短信通", popup)
                p_info.exec_()
            else:
                p_info = InformationPopup("修改成功!", popup)
                p_info.exec_()
                popup.close()
                self.content_label.setText(popup.text_edit.toHtml())  # 设置修改后的内容
        popup = self.sender()
        # 发送修改的网络请求
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "short-message/{}/".format(self.msg_id)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        body_data = {"message_content": content[5:]}
        reply = network_manager.put(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(modify_finished)

    def delete_short_message(self):
        """ 删除当前这条短信通 """
        p = WarningPopup("确定删除这条短信通吗?\n删除后将不可恢复!", self)
        p.confirm_operate.connect(self.confirm_delete_short_message)
        p.exec_()

    def confirm_delete_short_message(self):
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + 'short-message/{}/'.format(self.msg_id)
        user_token = get_user_token()
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("Authorization".encode("utf-8"), user_token.encode("utf-8"))
        reply = network_manager.deleteResource(request)
        reply.finished.connect(self.delete_message_reply)

    def delete_message_reply(self):
        """ 删除本条短信通返回 """
        reply = self.sender()
        if reply.error():
            logger.error("删除短信通错误:{}".format(reply.error()))
            p = InformationPopup("删除失败!\n您不能对他人的短信通进行这个操作!", self)
            p.exec_()
        else:
            p = InformationPopup("删除成功!", self)
            p.exec_()
            self.deleteLater()
        reply.deleteLater()


class ContentWidget(QWidget):
    def __init__(self, current_datetime,  *args, **kwargs):
        super(ContentWidget, self).__init__(*args, **kwargs)
        self.current_datetime = current_datetime
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(3, 0, 5, 0))
        main_layout.addStretch()
        self.setLayout(main_layout)

        self.setStyleSheet(
            "#contentLabel{background-color:rgb(245,245,245);padding:2px 3px 8px 8px;border-radius:5px;}"
            "#contentLabel:hover{background-color:rgb(235,235,235);padding:2px 3px 8px 8px;border-radius:5px;}"
        )

        self.get_short_message()

    def get_short_message(self):
        """ 获取今日短信通数据 """
        network_message = getattr(qApp, "_network")
        url = SERVER_API + "short-message/?start_time={}".format(self.current_datetime)
        reply = network_message.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.day_short_message_reply)

    def day_short_message_reply(self):
        """ 今日短信通数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_day_short_message(data["short_messages"])

    def show_day_short_message(self, contents):
        """ 新增最新短信通 """
        for index, content_item in enumerate(contents):
            content_label = ContentSignalLabel(content_item["content"], content_item["id"],self)
            content_label.setObjectName("contentLabel")
            self.layout().insertWidget(0, content_label)


class ShortMessageAdmin(ShortMessageAdminUI):
    def __init__(self, *args, **kwargs):
        super(ShortMessageAdmin, self).__init__(*args, **kwargs)
        self.query_button.clicked.connect(self.query_today_message)

    def query_today_message(self):
        """ 查询当前今日的所有短信通数据 """
        start_time = self.date_edit.text() + "T00:00:00"
        # 今日内容控件
        content_widget = ContentWidget(start_time)
        self.scroll_area.setWidget(content_widget)
