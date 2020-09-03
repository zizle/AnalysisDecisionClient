# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
from PyQt5.QtWidgets import QLineEdit, QFileDialog


class FilePathLineEdit(QLineEdit):
    def __init__(self,*args):
        super(FilePathLineEdit, self).__init__(*args)
        self.setReadOnly(True)
        self.setPlaceholderText("点击选择文件")

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择文件', '', "PDF files(*.pdf)")
        self.setText(file_path)


class FolderPathLineEdit(QLineEdit):
    def __init__(self,*args):
        super(FolderPathLineEdit, self).__init__(*args)
        self.setReadOnly(True)
        self.setPlaceholderText("点击选择文件夹路径")

    def mousePressEvent(self, event):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.setText(folder_path + "/")


class ImagePathLineEdit(QLineEdit):
    def __init__(self,*args):
        super(ImagePathLineEdit, self).__init__(*args)
        self.setReadOnly(True)
        self.setPlaceholderText("点击选择图片")

    def mousePressEvent(self, event):
        image_path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', "image PNG(*.png)")
        if image_path:
            # 对文件的大小进行限制
            self.setText(image_path)
