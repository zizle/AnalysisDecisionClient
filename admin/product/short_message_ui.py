# _*_ coding:utf-8 _*_
# @File  : short_message_ui.py
# @Time  : 2020-09-18 15:48
# @Author: zizle

""" 短信通管理后台 """
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QScrollArea, QFrame, QTextEdit,
                             QDialog)
from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtGui import QPalette


class ShortMessageAdminUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ShortMessageAdminUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        opt_layout.addWidget(self.date_edit)

        self.query_button = QPushButton("查询", self)
        opt_layout.addWidget(self.query_button)
        opt_layout.addStretch()

        main_layout.addLayout(opt_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)


class ModifyMessagePopup(QDialog):
    request_modify = pyqtSignal(str)

    def __init__(self,*args, **kwargs):
        super(ModifyMessagePopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("修改内容")
        self.setMinimumWidth(470)
        self.setAttribute(Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout()
        self.text_edit = QTextEdit(self)
        main_layout.addWidget(self.text_edit)

        self.confirm_button = QPushButton("确定", self)
        self.confirm_button.clicked.connect(self.confirm_modify)
        main_layout.addWidget(self.confirm_button, alignment=Qt.AlignRight)

        self.setLayout(main_layout)

    def confirm_modify(self):
        content = self.text_edit.toPlainText()
        self.request_modify.emit(content)

