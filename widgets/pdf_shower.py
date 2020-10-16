# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------

import fitz
import chardet
import requests
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QScrollArea,QVBoxLayout, QDialog
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QMargins, QSize


# PDF文件内容直显
class PDFContentShower(QScrollArea):
    def __init__(self, file, *args, **kwargs):
        super(PDFContentShower, self).__init__(*args, **kwargs)
        self.file = file
        # auth doc type
        # scroll
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # content
        self.page_container = QWidget(self)
        self.page_container.setLayout(QVBoxLayout(self))
        self.page_container.setObjectName('pageContainer')
        # initial data
        self.add_pages()
        # add to show
        self.setWidget(self.page_container)

        # 设置滚动条样式
        with open("media/ScrollBar.qss", "rb") as fp:
            content = fp.read()
            encoding = chardet.detect(content) or {}
            content = content.decode(encoding.get("encoding") or "utf-8")
        self.setStyleSheet(content + 'QScrollArea{border:none;}')

    def add_pages(self):
        # 请求文件
        if not self.file:
            message_label = QLabel('没有文件.')
            self.page_container.layout().addWidget(message_label)
            return
        try:
            response = requests.get(self.file)
            doc = fitz.Document(filename='a', stream=response.content)
        except Exception as e:
            message_label = QLabel('获取文件内容失败.\n{}'.format(e))
            self.page_container.layout().addWidget(message_label)
            return
        for page_index in range(doc.pageCount):
            page = doc.loadPage(page_index)
            page_label = QLabel()
            # page_label.setMinimumSize(self.width() - 20, self.height())  # 设置label大小
            # show PDF content
            zoom_matrix = fitz.Matrix(1.5, 1.5)  # 图像缩放比例
            pagePixmap = page.getPixmap(
                matrix=zoom_matrix,
                alpha=False)
            imageFormat = QImage.Format_RGB888  # get image format
            pageQImage = QImage(
                pagePixmap.samples,
                pagePixmap.width,
                pagePixmap.height,
                pagePixmap.stride,
                imageFormat)  # init QImage
            page_map = QPixmap()
            page_map.convertFromImage(pageQImage)
            page_label.setPixmap(page_map)
            page_label.setScaledContents(True)  # pixmap resize with label
            self.page_container.layout().addWidget(page_label)


# PDF文件内容弹窗
class PDFContentPopup(QDialog):
    def __init__(self, title, file, *args, **kwargs):
        super(PDFContentPopup, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.file = file
        self.file_name = title
        # auth doc type
        self.setWindowTitle(title)
        self.resize(925, 600)
        # self.download = QPushButton("下载PDF", self)
        # self.download.setIcon(QIcon('media/download-file.png'))
        self.setWindowIcon(QIcon("media/reader.png"))
        # scroll
        scroll_area = QScrollArea()
        scroll_area.setContentsMargins(QMargins(0, 0, 0, 0))
        scroll_area.setParent(self)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # content
        self.page_container = QWidget(self)
        container_layout = QVBoxLayout()  # 页面布局
        # 计算大小(设置了label范围890-895)
        container_layout.setContentsMargins(QMargins(10, 5, 10, 5))  # 右边 页面距离10
        self.page_container.setLayout(container_layout)
        layout = QVBoxLayout()  # 主布局
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        layout.setParent(self)
        # initial data
        self.add_pages()
        # add to show
        scroll_area.setWidget(self.page_container)
        scroll_area.setStyleSheet("border:none")
        scroll_area.horizontalScrollBar().setStyleSheet(
            "QScrollBar:horizontal{background:transparent;height:10px;margin:0px;}"
            "QScrollBar:horizontal:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:horizontal{background:rgba(0,0,0,50);height:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:horizontal:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-page:horizontal{height:10px;background:transparent;}"
            "QScrollBar::sub-line:horizontal{width:0px}"
            "QScrollBar::add-line:horizontal{width:0px}"
        )
        scroll_area.verticalScrollBar().setStyleSheet(
            "QScrollBar:vertical{background: transparent; width:10px;margin: 0px;}"
            "QScrollBar:vertical:hover{background:rgba(0,0,0,30);border-radius:5px}"
            "QScrollBar::handle:vertical{background: rgba(0,0,0,50);width:10px;border-radius:5px;border:none}"
            "QScrollBar::handle:vertical:hover{background:rgba(0,0,0,100)}"
            "QScrollBar::add-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-page:vertical{width:10px;background:transparent;}"
            "QScrollBar::sub-line:vertical{height:0px}"
            "QScrollBar::add-line:vertical{height:0px}"
        )
        # add layout
        # layout.addWidget(self.download, alignment=Qt.AlignLeft)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def add_pages(self):
        # 请求文件
        if not self.file:
            message_label = QLabel('没有文件.', self)
            self.page_container.layout().addWidget(message_label)
            return
        try:
            response = requests.get(self.file)
            doc = fitz.Document(filename=self.file_name, stream=response.content)
        except Exception as e:
            message_label = QLabel('获取文件内容失败.', self)
            self.page_container.layout().addWidget(message_label)
            return
        for page_index in range(doc.pageCount):
            page = doc.loadPage(page_index)
            page_label = QLabel()
            # 设置label大小:宽-左侧距离10-右侧距离10-右侧滚东条10
            # show PDF content
            zoom_matrix = fitz.Matrix(1.5, 1.5)  # 图像缩放比例 (893-894)
            pagePixmap = page.getPixmap(
                matrix=zoom_matrix,
                alpha=False)
            if pagePixmap.width >= 895:
                page_label.setFixedWidth(895)
            elif pagePixmap.width < 890:
                page_label.setFixedWidth(890)
            else:
                page_label.setFixedWidth(pagePixmap.width)  # 只有设置这个宽度才会清晰
            imageFormat = QImage.Format_RGB888  # get image format
            pageQImage = QImage(
                pagePixmap.samples,
                pagePixmap.width,
                pagePixmap.height,
                pagePixmap.stride,
                imageFormat)  # init QImage
            page_map = QPixmap()

            page_map.convertFromImage(pageQImage)
            page_label.setPixmap(page_map)
            page_label.setScaledContents(True)  # pixmap resize with label
            self.page_container.layout().addWidget(page_label, alignment=Qt.AlignHCenter)
        doc.close()
