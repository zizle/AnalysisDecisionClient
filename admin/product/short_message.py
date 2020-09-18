# _*_ coding:utf-8 _*_
# @File  : short_message.py
# @Time  : 2020-09-18 15:56
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QMargins, Qt, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from settings import SERVER_API
from .short_message_ui import ShortMessageAdminUI


class ContentSignalLabel(QWidget):
    def __init__(self, content, msg_id,  *args, **kwargs):
        super(ContentSignalLabel, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.msg_id = msg_id
        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        opt_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        delete_button = QPushButton("删除", self)
        delete_button.clicked.connect(self.delete_short_message)
        opt_layout.addWidget(delete_button, alignment=Qt.AlignRight)

        content_label = QLabel(content, self)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(content_label)
        main_layout.addLayout(opt_layout)
        self.setLayout(main_layout)

    def delete_short_message(self):
        """ 删除当前这条短信通 """
        print(self.msg_id)
        self.deleteLater()


class ContentWidget(QWidget):
    def __init__(self, current_datetime,  *args, **kwargs):
        super(ContentWidget, self).__init__(*args, **kwargs)
        self.current_datetime = current_datetime
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(3, 0, 5, 0))
        main_layout.addStretch()
        self.setLayout(main_layout)

        self.setStyleSheet(
            "#contentLabel{background-color:rgb(240,240,240);padding:2px 3px 8px 8px;border-radius:5px;}"
        )
        self.get_short_message()

    def get_short_message(self):
        """ 获取今日短信通数据 """
        network_message = getattr(qApp, "_network")
        url = SERVER_API + "short_message/?start_time={}".format(self.current_datetime)
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
