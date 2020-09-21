# _*_ coding:utf-8 _*_
# @File  : short_message.py
# @Time  : 2020-09-15 13:40
# @Author: zizle

""" 短信通业务逻辑 """
import json
from datetime import datetime
from PyQt5.QtWidgets import qApp, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt, QMargins, QUrl
from PyQt5.QtNetwork import QNetworkRequest
from settings import SERVER_API
from .short_message_ui import ShortMessageUI


class ContentWidget(QWidget):
    """ 内容控件 """
    def __init__(self, current_datetime, timer_start=False, *args, **kwargs):
        super(ContentWidget, self).__init__(*args, **kwargs)
        self.current_datetime = current_datetime
        self.auto_request_timer = QTimer(self)  # 定时请求数据
        self.auto_request_timer.timeout.connect(self._get_last_short_message)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(3, 0, 5, 0))
        main_layout.addStretch()
        self.setLayout(main_layout)

        self._get_last_short_message()
        if timer_start:
            self.auto_request_timer.start(30000)
        self.setStyleSheet(
            "#contentLabel{background-color:rgb(240,240,240);padding:2px 3px 8px 8px;border-radius:5px;}"
            "#contentLabel:hover{background-color:rgb(230,230,230);padding:2px 3px 8px 8px;border-radius:5px;}"
        )

    def _get_last_short_message(self):
        """ 获取最新短信通 """
        # 请求比self.last_datetime大的数据(服务器仅返回当天的数据)
        # print("self.current_datetime: {}".format(self.current_datetime))
        network_message = getattr(qApp, "_network")
        url = SERVER_API + "short-message/?start_time={}".format(self.current_datetime)
        reply = network_message.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_short_message_reply)

    def latest_short_message_reply(self):
        """ 最新的短信通数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.insert_latest_short_message(data["short_messages"])

    def insert_latest_short_message(self, contents):
        """ 新增最新短信通 """
        for index, content_item in enumerate(contents):
            content_label = QLabel(content_item["content"], self)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_label.setObjectName("contentLabel")

            self.layout().insertWidget(0, content_label)
            if index == len(contents) - 1:
                self.current_datetime = content_item["create_time"]


class ShortMessage(ShortMessageUI):
    def __init__(self, *args, **kwargs):
        super(ShortMessage, self).__init__(*args, **kwargs)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.refresh_animation_text)

        # 默认添加今日的内容控件
        current_datetime = datetime.today().strftime("%Y-%m-%dT00:00:00")
        content_widget = ContentWidget(current_datetime, timer_start=True)
        self.animation_timer.start(600)
        self.scroll_area.setWidget(content_widget)
        self.date_edit.dateChanged.connect(self.current_date_changed)

    def refresh_animation_text(self):
        """ 资讯持续更新中 """
        tips = self.animation_text.text()
        tip_points = tips.split(' ')[1]
        if len(tip_points) > 5:
            self.animation_text.setText("资讯持续更新中 ")
        else:
            self.animation_text.setText("资讯持续更新中 " + "·" * (len(tip_points) + 1))

    def current_date_changed(self, date):
        """ 当前时间发生改变 """
        date_edit_text = self.date_edit.text()
        current_date = datetime.strptime(date_edit_text, "%Y-%m-%d")
        current_date_str = current_date.strftime("%Y-%m-%dT00:00:00")
        week_name = self.WEEKS.get(current_date.strftime("%w"))
        self.current_date.setText(date_edit_text + week_name)

        if current_date_str == datetime.today().strftime("%Y-%m-%dT00:00:00"):
            timer_start = True
            self.animation_text.show()
            if not self.animation_timer.isActive():
                self.animation_timer.start(600)
        else:
            timer_start = False
            self.animation_text.hide()
            if self.animation_timer.isActive():
                self.animation_timer.stop()
        self.animation_text.setText("资讯持续更新中 ")
        content_widget = ContentWidget(current_date_str, timer_start=timer_start)
        self.scroll_area.setWidget(content_widget)

