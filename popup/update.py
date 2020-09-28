# _*_ coding:utf-8 _*_
# @File  : update.py
# @Time  : 2020-09-14 11:13
# @Author: zizle

""" 新版本更新弹窗 """
from PyQt5.QtWidgets import QDialog, QVBoxLayout,QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal


class NewVersionPopup(QDialog):
    to_update = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(NewVersionPopup, self).__init__(*args, *kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        main_layout = QVBoxLayout()
        self.setWindowTitle("新版本")
        label = QLabel("系统检测到新版本可更新!\n使用新功能和避免原功能不可用,建议更新。", self)
        main_layout.addWidget(label)
        self.ignore_button = QPushButton("本次忽略", self)
        self.ignore_button.clicked.connect(self.close)
        self.update_button = QPushButton("前往更新", self)
        self.update_button.clicked.connect(self.to_update_page)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ignore_button)
        button_layout.addWidget(self.update_button)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def to_update_page(self):
        self.hide()
        self.to_update.emit()
        self.close()

