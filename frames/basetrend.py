# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import json
import requests
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QMargins, Qt
from widgets import ScrollFoldedBox
import settings


# 基本分析主页
class TrendPage(QWidget):
    def __init__(self, *args, **kwargs):
        super(TrendPage, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 1))
        layout.setSpacing(0)
        self.variety_folded = ScrollFoldedBox()
        self.variety_folded.left_mouse_clicked.connect(self.variety_clicked)
        layout.addWidget(self.variety_folded, alignment=Qt.AlignLeft)

        self.web_charts = QWebEngineView(self)

        layout.addWidget(self.web_charts)

        self.setLayout(layout)
        # 设置折叠窗的样式
        self.variety_folded.setFoldedStyleSheet("""
        QScrollArea{
            border: none;
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
        self._get_all_charts()

    def resizeEvent(self, event):
        # 设置折叠窗的大小
        box_width = self.parent().width() * 0.228
        self.variety_folded.setFixedWidth(box_width + 5)
        self.variety_folded.setBodyHorizationItemCount()
        self.web_charts.setMinimumWidth(self.parent().width() - box_width)  # 设置页面显示的大小
        self.web_charts.reload()

    def _get_all_charts(self, variety_id=0):
        self.web_charts.load(QUrl(settings.SERVER_ADDR + 'trend/charts/?is_render=1' + '&variety=' + str(variety_id)))

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
                    body.addButton(sub_item['id'], sub_item['name'])
            self.variety_folded.container.layout().addStretch()

    # 点击了品种,请求当前品种下的品种页显示图表
    def variety_clicked(self, vid, text):
        self._get_all_charts(variety_id=vid)

