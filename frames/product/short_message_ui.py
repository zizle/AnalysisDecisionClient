# _*_ coding:utf-8 _*_
# @File  : short_message_ui.py
# @Time  : 2020-09-15 13:39
# @Author: zizle
""" 短信通 """
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDateEdit, QScrollArea, QFrame
from PyQt5.QtCore import QDate, QMargins
from PyQt5.QtGui import QPalette


class ShortMessageUI(QWidget):
    WEEKS = {
        "1": " 星期一",
        "2": " 星期二",
        "3": " 星期三",
        "4": " 星期四",
        "5": " 星期五",
        "6": " 星期六",
        "7": " 星期日",
    }

    def __init__(self, *args, **kwargs):
        super(ShortMessageUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(1, 1, 1, 1))
        option_layout = QHBoxLayout()

        today = datetime.today()
        today_str = today.strftime("%Y-%m-%d")
        week_name = self.WEEKS.get(today.strftime("%w"))

        self.current_date = QLabel(today_str + week_name, self)
        option_layout.addWidget(self.current_date)

        self.animation_text = QLabel("资讯持续更新中 ", self)
        option_layout.addWidget(self.animation_text)
        option_layout.addStretch()
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        option_layout.addWidget(self.date_edit)

        main_layout.addLayout(option_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setBackgroundRole(QPalette.Light)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)
        self.current_date.setObjectName("currentDate")
        self.animation_text.setObjectName("animationText")

        self.scroll_area.verticalScrollBar().setStyleSheet(
            "QScrollBar:vertical{background: transparent; width:10px;margin: 0px;}"
            "QScrollBar:vertical:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:vertical{background: rgba(0,0,0,50);width:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:vertical:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-line:vertical{height:0px}"
            "QScrollBar::add-line:vertical{height:0px}"
        )

        self.setStyleSheet(
            "#currentDate{font-size:17px;font-weight:bold}"
            "#animationText{color:rgb(233,66,66);padding-left:8px};"
        )

