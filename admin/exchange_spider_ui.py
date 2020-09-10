# _*_ coding:utf-8 _*_
# @File  : exchange_spider_ui.py
# @Time  : 2020-07-22 20:47
# @Author: zizle

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton, QDateEdit
from PyQt5.QtCore import QMargins, Qt, QDate, QSize
from PyQt5.QtGui import QBrush, QPalette, QPixmap
from components.exchange_tree import ExchangeLibTree


class ExchangeSpiderUI(QWidget):
    """ 数据抓取主页面 """
    def __init__(self, *args, **kwargs):
        super(ExchangeSpiderUI, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(2, 0, 2, 1))
        main_splitter = QSplitter(self)
        main_splitter.setHandleWidth(1)
        self.tree_widget = ExchangeLibTree(self)
        main_splitter.addWidget(self.tree_widget)

        action_splitter = QSplitter(Qt.Vertical, self)
        action_splitter.setHandleWidth(1)

        spider_widget = QWidget(self)
        spider_widget.setAutoFillBackground(True)
        palette = QPalette()
        pix = QPixmap("images/spider_bg.png")
        pix = pix.scaled(QSize(700, 700), Qt.KeepAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pix))
        spider_widget.setPalette(palette)

        spider_layout = QVBoxLayout()

        tips_layout = QHBoxLayout()
        tips_layout.setSpacing(1)
        tips_layout.addWidget(QLabel("当前交易所:", self))
        self.spider_exchange_button = QPushButton("未选择", self)
        tips_layout.addWidget(self.spider_exchange_button)

        tips_layout.addWidget(QLabel(self))
        tips_layout.addWidget(QLabel("当前操作:", self))
        self.spider_action_button = QPushButton("未选择", self)
        tips_layout.addWidget(self.spider_action_button)

        tips_layout.addWidget(QLabel(self))
        tips_layout.addWidget(QLabel("选择日期:", self))
        self.spider_date_edit = QDateEdit(QDate.currentDate(), self)
        self.spider_date_edit.setCalendarPopup(True)
        self.spider_date_edit.setDisplayFormat("yyyy-MM-dd")
        tips_layout.addWidget(self.spider_date_edit)

        tips_layout.addWidget(QLabel(self))
        self.spider_start_button = QPushButton("开始", self)
        tips_layout.addWidget(self.spider_start_button)
        tips_layout.addStretch()

        spider_layout.addLayout(tips_layout)

        self.spider_status = QLabel("等待开始抓取", self)
        self.spider_status.setWordWrap(True)
        self.spider_status.setAlignment(Qt.AlignCenter)

        spider_layout.addWidget(self.spider_status)

        spider_widget.setLayout(spider_layout)

        action_splitter.addWidget(spider_widget)

        # 解析部分
        parser_widget = QWidget(self)
        parser_widget.setAutoFillBackground(True)
        palette = QPalette()
        pix = QPixmap("images/parser_bg.png")
        pix = pix.scaled(QSize(700, 700), Qt.KeepAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pix))
        parser_widget.setPalette(palette)

        parser_layout = QVBoxLayout()

        tips_layout = QHBoxLayout()
        tips_layout.setSpacing(1)
        tips_layout.addWidget(QLabel("当前交易所:", self))
        self.parser_exchange_button = QPushButton("未选择", self)
        tips_layout.addWidget(self.parser_exchange_button)

        tips_layout.addWidget(QLabel(self))
        tips_layout.addWidget(QLabel("当前操作:", self))
        self.parser_action_button = QPushButton("未选择", self)
        tips_layout.addWidget(self.parser_action_button)

        tips_layout.addWidget(QLabel(self))
        tips_layout.addWidget(QLabel("选择日期:", self))
        self.parser_date_edit = QDateEdit(QDate.currentDate(), self)
        self.parser_date_edit.setCalendarPopup(True)
        self.parser_date_edit.setDisplayFormat("yyyy-MM-dd")
        tips_layout.addWidget(self.parser_date_edit)

        tips_layout.addWidget(QLabel(self))
        self.parser_start_button = QPushButton("开始", self)
        tips_layout.addWidget(self.parser_start_button)
        tips_layout.addStretch()

        parser_layout.addLayout(tips_layout)

        self.parser_status = QLabel("等待开始解析", self)
        self.parser_status.setAlignment(Qt.AlignCenter)
        parser_layout.addWidget(self.parser_status)

        parser_widget.setLayout(parser_layout)

        action_splitter.addWidget(parser_widget)

        main_splitter.addWidget(action_splitter)

        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 6)

        layout.addWidget(main_splitter)
        self.setLayout(layout)

        main_splitter.setObjectName("mainSplitter")
        action_splitter.setObjectName("actionSplitter")

        self.spider_exchange_button.setObjectName("tipButton")
        self.spider_action_button.setObjectName("tipButton")
        self.spider_status.setObjectName("spiderStatus")

        self.parser_exchange_button.setObjectName("tipButton")
        self.parser_action_button.setObjectName("tipButton")
        self.parser_status.setObjectName("parserStatus")

        self.setStyleSheet(
            "#mainSplitter::handle{background-color:rgba(50,50,50,100)}"
            "#actionSplitter::handle{background-color:rgba(50,50,50,100)}"
            "#tipButton{border:none;color:rgb(220,100,100)}"
            "#spiderStatus,#parserStatus{font-size:16px;font-weight:bold;color:rgb(230,50,50)}"
        )

