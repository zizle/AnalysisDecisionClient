# _*_ coding:utf-8 _*_
# @File  : advertisement_ui.py
# @Time  : 2020-10-12 15:50
# @Author: zizle
from PyQt5.QtWidgets import (QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QPushButton, QFrame, QLineEdit,
                             QGridLayout, QLabel, QComboBox, QHeaderView)
from PyQt5.QtCore import Qt
from widgets.path_edit import ImagePathLineEdit, FilePathLineEdit


class HomepageAdAdminUI(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(HomepageAdAdminUI, self).__init__(*args, **kwargs)
        self.ad_table = QTableWidget(self)
        self.ad_table.verticalHeader().hide()
        self.ad_table.setFrameShape(QFrame.NoFrame)
        self.ad_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.ad_table.setColumnCount(9)
        self.ad_table.setHorizontalHeaderLabels(["编号", "标题", "类型", "图片", "文件", "网址", "内容", "备注", "启用"])
        self.ad_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ad_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.addTab(self.ad_table, "广告管理")

        new_ad_widget = QWidget(self)
        create_layout = QGridLayout()
        create_layout.addWidget(QLabel("标题：", self), 0, 0)
        self.new_title = QLineEdit(self)
        self.new_title.setPlaceholderText("在此输入广告的标题")
        create_layout.addWidget(self.new_title, 0, 1)

        create_layout.addWidget(QLabel("类型：", self), 1, 0)
        self.ad_type = QComboBox(self)
        create_layout.addWidget(self.ad_type)

        self.file_label = QLabel("文件：", self)
        create_layout.addWidget(self.file_label, 2, 0)
        self.filepath_edit = FilePathLineEdit(self)
        self.filepath_edit.setPlaceholderText("点击选择pdf文件")
        create_layout.addWidget(self.filepath_edit, 2, 1)

        self.content_label = QLabel("内容：", self)
        create_layout.addWidget(self.content_label, 3, 0)
        self.content_edit = QLineEdit(self)
        self.content_edit.setPlaceholderText("在此输入要显示的内容")
        create_layout.addWidget(self.content_edit, 3, 1)

        self.web_label = QLabel("网址：", self)
        create_layout.addWidget(self.web_label, 4, 0)
        self.web_edit = QLineEdit(self)
        self.web_edit.setPlaceholderText("在此输入要跳转的网址")
        create_layout.addWidget(self.web_edit, 4, 1)

        create_layout.addWidget(QLabel("图片：", self), 5, 0)
        self.imagepath_edit = ImagePathLineEdit(self)
        self.imagepath_edit.setPlaceholderText("点击选择图片")
        create_layout.addWidget(self.imagepath_edit, 5, 1)

        self.tip_label = QLabel("<div style=color:rgb(233,66,66)>创建完成默认运营可见,确认无误后到广告管理公开。</div>")
        create_layout.addWidget(self.tip_label, 6, 1)

        self.create_button = QPushButton("确定创建", self)
        create_layout.addWidget(self.create_button, 6, 1, alignment=Qt.AlignRight)

        new_ad_widget.setLayout(create_layout)
        self.addTab(new_ad_widget, "新建广告")



