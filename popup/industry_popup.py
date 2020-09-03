# _*_ coding:utf-8 _*_
# @File  : industry_popup.py
# @Time  : 2020-09-03 20:30
# @Author: zizle
""" 行业数据的弹窗U组件 """
import os
import sqlite3
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from widgets.path_edit import FolderPathLineEdit
from utils.client import get_client_uuid
from settings import BASE_DIR


class UpdateFolderPopup(QDialog):
    """ 更新数据的文件夹配置 """
    successful_signal = pyqtSignal(str)

    def __init__(self, variety_en, variety_text, group_id, group_text, *args, **kwargs):
        super(UpdateFolderPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.variety_en = variety_en
        self.group_id = group_id

        self.setWindowTitle("配置「" + variety_text + "」的更新路径")

        main_layout = QGridLayout()

        main_layout.addWidget(QLabel("品种:", self), 0, 0)
        main_layout.addWidget(QLabel(variety_text, self), 0, 1)

        main_layout.addWidget(QLabel("组别:"), 1, 0)
        main_layout.addWidget(QLabel(group_text), 1, 1)

        main_layout.addWidget(QLabel("路径:"), 2, 0)
        self.folder_edit = FolderPathLineEdit(self)
        main_layout.addWidget(self.folder_edit)

        self.confirm_button = QPushButton("确定", self)
        self.confirm_button.clicked.connect(self.confirm_current_folder)
        main_layout.addWidget(self.confirm_button, 3, 1, alignment=Qt.AlignRight)

        self.setLayout(main_layout)
        self.setMinimumWidth(370)
        self.setFixedHeight(155)

    def confirm_current_folder(self):
        """ 确定当前配置 """
        # 打开sqlite3进行数据的保存
        folder_path = self.folder_edit.text()
        if not folder_path:
            return
        insert_data = [get_client_uuid(), self.variety_en, self.group_id, folder_path]
        db_path = os.path.join(BASE_DIR, "dawn/local_data.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT CLIENT,VARIETY_EN,GROUP_ID FROM UPDATE_FOLDER "
            "WHERE CLIENT=? AND VARIETY_EN=? AND GROUP_ID=?;",
            (insert_data[0], insert_data[1], insert_data[2])
        )
        if cursor.fetchone():  # 更新
            cursor.execute(
                "UPDATE UPDATE_FOLDER SET FOLDER=? "
                "WHERE CLIENT=? AND VARIETY_EN=? AND GROUP_ID=?;",
                (insert_data[3], insert_data[0], insert_data[1], insert_data[2])
            )
        else:  # 新建
            cursor.execute(
                "INSERT INTO UPDATE_FOLDER (CLIENT,VARIETY_EN,GROUP_ID,FOLDER) "
                "VALUES (?,?,?,?);",
                insert_data
            )
        conn.commit()
        cursor.close()
        conn.close()
        self.successful_signal.emit("调整配置成功!")



