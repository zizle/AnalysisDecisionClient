# _*_ coding:utf-8 _*_
# @File  : short_message.py
# @Time  : 2020-09-15 13:40
# @Author: zizle

""" 短信通业务逻辑 """
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt, QMargins
from PyQt5.QtGui import QFont
from .short_message_ui import ShortMessageUI


class ContentWidget(QWidget):
    """ 内容控件 """
    def __init__(self, current_datetime, *args, **kwargs):
        super(ContentWidget, self).__init__(*args, **kwargs)
        self.current_datetime = current_datetime
        self.auto_request_timer = QTimer(self)  # 定时请求数据
        self.auto_request_timer.timeout.connect(self._get_last_short_message)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(3, 0, 5, 0))
        main_layout.addStretch()
        self.setLayout(main_layout)

        self._get_last_short_message()
        self.auto_request_timer.start(10000)
        self.setStyleSheet(
            "#contentLabel{background-color:rgb(240,240,240);padding:2px 3px 8px 8px;border-radius:5px;}"
        )

    def _get_last_short_message(self):
        """ 获取最新短信通 """
        # 请求比self.last_datetime大比其多一天小的数据
        next_date_time = datetime.strptime(self.current_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
        next_date_time = next_date_time.strftime("%Y-%m-%d 00:00:00")
        print(self.current_datetime, next_date_time)

        contents = [
            {"id": 1, "create_time": "2020-09-02 15:12:23", "content":
                "<div style='text-indent:30px;line-height:25px;font-size:13px;'><span style='font-size:15px;font-weight:bold;color:rgb(233,20,20);'>15:12</span> 这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。</div>"
             },
            {"id": 2, "create_time": "2020-09-02 15:16:23", "content":
                "<div style='text-indent:30px;line-height:25px;font-size:13px'><span style='font-size:15px;font-weight:bold;color:rgb(233,20,20);'>15:12</span> 这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。</div>"
             },
            {"id": 3, "create_time": "2020-09-02 15:21:22", "content":
                "<div style='text-indent:30px;line-height:25px;font-size:13px;'><span style='font-size:15px;font-weight:bold;color:rgb(233,20,20);'>15:12</span> 这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。这是短信通的内容。</div>"
             },
        ]
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
        current_datetime = datetime.today().strftime("%Y-%m-%d 00:00:00")
        content_widget = ContentWidget(current_datetime)

        self.scroll_area.setWidget(content_widget)

        self.animation_timer.start(600)
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
        current_date_str = current_date.strftime("%Y-%m-%d 00:00:00")
        print(current_date)
        week_name = self.WEEKS.get(current_date.strftime("%w"))
        self.current_date.setText(date_edit_text + week_name)

        content_widget = ContentWidget(current_date_str)
        self.scroll_area.setWidget(content_widget)

