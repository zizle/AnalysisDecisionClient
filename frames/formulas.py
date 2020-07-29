# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import os
import json
import requests
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import QUrl, QMargins
from widgets import ScrollFoldedBox
import settings


# 公式计算页面
class FormulasCalculate(QWidget):
    def __init__(self, *args, **kwargs):
        super(FormulasCalculate, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        # 左边是品种的显示折叠窗
        self.variety_folded = ScrollFoldedBox()
        self.variety_folded.left_mouse_clicked.connect(self.variety_clicked)
        layout.addWidget(self.variety_folded)
        # 右侧显示页面的web浏览器
        self.web_browser = QWebEngineView(self)
        layout.addWidget(self.web_browser)
        self.setLayout(layout)
        # 设置折叠窗的样式
        self.variety_folded.setFoldedStyleSheet("""
        QScrollArea{
            border:none;
        }
        #foldedBox{
            border-right: 1px solid rgb(180, 180, 180);
        }
        #foldedHead{
            background-color: rgb(145,202,182);
            border-bottom: 1px solid rgb(200,200,200);
            border-right: 1px solid rgb(180, 180, 180);
            max-height: 30px;
        }
        #headLabel{
            padding:8px 5px;
            font-weight: bold;
            font-size: 15px;
        }
        #foldedBody{
            background-color: rgb(240, 240, 240);
            border-right: 1px solid rgb(180, 180, 180);
        }
        /*折叠窗内滚动条样式*/
        #foldedBox QScrollBar:vertical{
            width: 5px;
            background: transparent;
        }
        #foldedBox QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 30);
            width: 5px;
            border-radius: 5px;
            border: none;
        }
        #foldedBox QScrollBar::handle:vertical:hover,QScrollBar::handle:horizontal:hover {
            background: rgba(0, 0, 0, 80);
        }
        """)

        # web页面加载
        self.web_browser.page().load(QUrl("file:///pages/formulas/index.html"))

    def resizeEvent(self, event):
        # 设置折叠窗的大小
        box_width = self.parent().width() * 0.228
        self.variety_folded.setFixedWidth(box_width + 5)
        self.variety_folded.setBodyHorizationItemCount()

    # 获取所有品种组和品种
    def getGroupVarieties(self):
        try:
            r = requests.get(url=settings.SERVER_ADDR + 'variety/?way=group')
            if r.status_code != 200:
                raise ValueError('获取失败!')
            response = json.loads(r.content.decode('utf-8'))
        except Exception:
            pass
        else:
            for group_item in response['variety']:
                head = self.variety_folded.addHead(group_item['name'])
                body = self.variety_folded.addBody(head=head)
                for sub_item in group_item['subs']:
                    body.addButton(sub_item['id'], sub_item['name'], sub_item['name_en'])
            self.variety_folded.container.layout().addStretch()

    def variety_clicked(self, bid, head_text, v_en):
        # 拼接字符串
        # print(bid, head_text, v_en)
        file_path = os.path.join(settings.BASE_DIR, 'dawn/formulas.json')
        with open(file_path, "r", encoding="utf-8") as f:
            support_list = json.load(f)
        if v_en in support_list:
            page_file = "file:///pages/formulas/variety/calculate_{}.html".format(v_en)
        else:
            page_file = "file:///pages/formulas/variety/no_found.html"
        self.web_browser.load(QUrl(page_file))