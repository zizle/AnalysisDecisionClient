# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-09-09
# ---------------------------

""" 自定义消息弹窗 """
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QStyle
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

class InformationPopup(QDialog):
    def __init__(self, message, *args):
        super(InformationPopup, self).__init__(*args)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("提示")
        self.setFixedWidth(230)
        main_layout = QVBoxLayout()
        message_layout = QHBoxLayout()
        message_layout.setSpacing(5)
        icon_label = QLabel(self)
        icon_label.setFixedSize(50, 50)
        icon_label.setPixmap(QPixmap("media/icons/information.png"))
        icon_label.setScaledContents(True)
        message_layout.addWidget(icon_label, alignment=Qt.AlignLeft)
        message = "<div style=text-indent:24px;font-size:12px;line-height:18px;>" + message + "</div>"
        message_label = QLabel(message, self)
        message_label.setMinimumWidth(155)

        message_label.setWordWrap(True)
        message_layout.addWidget(message_label)
        main_layout.addLayout(message_layout)
        confirm_button = QPushButton("确定", self)
        confirm_button.clicked.connect(self.close)
        main_layout.addWidget(confirm_button, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.setLayout(main_layout)



