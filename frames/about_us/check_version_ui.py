# _*_ coding:utf-8 _*_
# @File  : check_version_ui.py
# @Time  : 2020-09-11 10:19
# @Author: zizle
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt


class CheckVersionUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(CheckVersionUI, self).__init__(*args, **kwargs)
        main_layout = QGridLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(QLabel("客户端号:", self), 0, 0)
        self.client_uuid = QLabel(self)
        self.client_uuid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(self.client_uuid, 0, 1, 1, 2)

        main_layout.addWidget(QLabel("当前版本:", self), 1, 0)
        self.current_version = QLabel(self)
        main_layout.addWidget(self.current_version, 1, 1, 1, 2)

        main_layout.addWidget(QLabel("最新版本:", self), 2, 0)
        self.last_version = QLabel("检查中...", self)
        main_layout.addWidget(self.last_version, 2, 1, 1, 2)

        main_layout.addWidget(QLabel("更新详情:", self), 3, 0, alignment=Qt.AlignTop)
        self.update_detail = QLabel(self)
        self.update_detail.setMaximumWidth(300)
        self.update_detail.setWordWrap(True)
        main_layout.addWidget(self.update_detail, 3, 1, 1, 2)

        self.update_right_now = QPushButton("立即更新")
        main_layout.addWidget(self.update_right_now, 4, 0, 1, 3)

        self.setLayout(main_layout)
