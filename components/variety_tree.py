# _*_ coding:utf-8 _*_
# @File  : variety_tree.py
# @Time  : 2020-09-03 9:44
# @Author: zizle
import json
from PyQt5.QtWidgets import qApp
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QUrl
from widgets.folded_box import ScrollFoldedBox
from settings import SERVER_API, logger


class VarietyTree(ScrollFoldedBox):
    def __init__(self, *args, **kwargs):
        super(VarietyTree, self).__init__(*args, **kwargs)
        self._get_all_variety()

        self.setFoldedStyleSheet(
            "QScrollArea{border: none;background-color:rgb(255,255,255)}"
            "#foldedBox{border-right: 1px solid rgb(180, 180, 180);}"
            "#foldedHead{background-color:rgb(145,202,182);border-bottom:1px solid rgb(200,200,200);border-right: 1px solid rgb(180, 180, 180);max-height: 30px;}"
            "#headLabel{padding:8px 5px;font-weight: bold;font-size: 15px;}"
            "#foldedBody{border-right: 1px solid rgb(180, 180, 180);}"
            "#foldedBox QScrollBar:vertical{width: 5px;background: transparent;}"
            "#foldedBox QScrollBar::handle:vertical {background: rgba(0, 0, 0, 30);width: 5px;border-radius: 5px;border:none;}"
            "#foldedBox QScrollBar::handle:vertical:hover,QScrollBar::handle:horizontal:hover {background: rgba(0, 0, 0, 80);}"
            )

    def _get_all_variety(self):
        """ 获取所有品种 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "variety/all/"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.all_variety_reply)

    def all_variety_reply(self):
        """ 获取品种数据返回 """
        reply = self.sender()
        if reply.error():
            logger.error("获取全部组及其品种失败了!{}".format(reply.error()))
        else:
            data = reply.readAll().data()
            data = json.loads(data.decode('utf-8'))
            self._fill_variety_tree(data['varieties'])

        reply.deleteLater()

    def _fill_variety_tree(self, varieties):
        """ 填充品种内容 """
        for group_name, group_item in varieties.items():
            head = self.addHead(group_name)
            body = self.addBody(head=head)
            for sub_item in group_item:
                body.addButton(id=sub_item["id"], name=sub_item['variety_name'], name_en=sub_item['variety_en'])
        self.container.layout().addStretch()

        self.setBodyHorizationItemCount()   # 手动调用填充内容

    def resizeEvent(self, event):
        """ 大小改变了 """
        self.setBodyHorizationItemCount()

