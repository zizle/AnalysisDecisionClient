# _*_ coding:utf-8 _*_
# @File  : cover.py
# @Time  : 2020-09-05 16:33
# @Author: zizle

""" 遮罩层 """

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import QTimer, Qt, QMargins


class CoverWidget(QWidget):
    def __init__(self, text, *args, **kwargs):
        super(CoverWidget, self).__init__(*args, **kwargs)
        self.text = text
        self.text_animation_timer = QTimer(self)
        self.text_animation_timer.timeout.connect(self.animation_text)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.text_label = QLabel(text, self)
        self.text_label.setAlignment(Qt.AlignCenter)

        opacity_effect = QGraphicsOpacityEffect(self)
        opacity_effect.setOpacity(0.7)
        self.setGraphicsEffect(opacity_effect)

        main_layout.addWidget(self.text_label)
        self.setLayout(main_layout)
        self.setStyleSheet("background-color:rgb(160,160,160)")
        self.text_label.setStyleSheet("font-size:14px;font-weight:bold;color:rgb(18,101,230)")

        self.text_animation_timer.start(400)

    def set_text(self, text):
        self.text = text
    
    def animation_text(self):
        tips = self.text_label.text()
        tip_points = tips.split(' ')[1]
        if len(tip_points) > 2:
            self.text_label.setText(self.text)
        else:
            self.text_label.setText(self.text + "·" * (len(tip_points) + 1))
        
    def hide(self):
        if self.text_animation_timer.isActive():
            self.text_animation_timer.stop()
        super(CoverWidget, self).hide()
        
    def show(self):
        if not self.text_animation_timer.isActive():
            self.text_animation_timer.start(400)
        super(CoverWidget, self).show()
