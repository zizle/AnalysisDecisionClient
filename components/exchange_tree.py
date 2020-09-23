# _*_ coding:utf-8 _*_
# @File  : exchange_tree.py
# @Time  : 2020-08-20 13:40
# @Author: zizle
# _*_ coding:utf-8 _*_
# @File  : exchange_tree.py
# @Time  : 2020-07-22 20:44
# @Author: zizle

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon


class ExchangeLibTree(QTreeWidget):
    """ 自定义树控件 """
    selected_signal = pyqtSignal(str, str)
    unselected_signal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ExchangeLibTree, self).__init__(*args, **kwargs)
        self.itemClicked.connect(self.item_clicked)
        # self.setIndentation(0)  # 设置子项不缩进
        self.header().hide()
        # self.setRootIsDecorated(False)
        self.setFocusPolicy(Qt.NoFocus)
        # self.setLayoutDirection(Qt.RightToLeft)
        self.setColumnCount(1)
        # 添加交易所数据
        lib = [
            {
                "id": "cffex", "name": "中国金融期货交易所", "logo": "media/icons/cffex_logo.png",
                "children": [
                    {"id": "daily", "name": "日交易数据", "logo": "media/icons/daily.png"},
                    {"id": "rank", "name": "日交易排名", "logo": "media/icons/rank.png"},
                ]
            },
            {
                "id": "shfe", "name": "上海期货交易所", "logo": "media/icons/shfe_logo.png",
                "children": [
                    {"id": "daily", "name": "日交易数据", "logo": "media/icons/daily.png"},
                    {"id": "rank", "name": "日交易排名", "logo": "media/icons/rank.png"},
                    {"id": "receipt", "name": "每日仓单", "logo": "media/icons/receipt.png"},
                ]
            },
            {
                "id": "czce", "name": "郑州商品交易所", "logo": "media/icons/czce_logo.png",
                "children": [
                        {"id": "daily", "name": "日交易数据", "logo": "media/icons/daily.png"},
                        {"id": "rank", "name": "日交易排名", "logo": "media/icons/rank.png"},
                        {"id": "receipt", "name": "每日仓单", "logo": "media/icons/receipt.png"},
                    ]
             },
            {
                "id": "dce", "name": "大连商品交易所", "logo": "media/icons/dce_logo.png",
                "children": [
                    {"id": "daily", "name": "日交易数据", "logo": "media/icons/daily.png"},
                    {"id": "rank", "name": "日交易排名", "logo": "media/icons/rank.png"},
                    {"id": "receipt", "name": "每日仓单", "logo": "media/icons/receipt.png"},
                ]
             },
        ]

        for item in lib:
            tree_item = QTreeWidgetItem(self)
            tree_item.setText(0, item["name"])
            setattr(tree_item, "id", item["id"])
            # tree_item.setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)
            tree_item.setIcon(0, QIcon(item["logo"]))
            for child_item in item["children"]:
                child = QTreeWidgetItem(tree_item)
                child.setText(0, child_item["name"])
                setattr(child, "id", child_item["id"])
                child.setIcon(0, QIcon(child_item["logo"]))
                # child.setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)
                tree_item.addChild(child)
        self.setObjectName("exchangeTree")
        self.setStyleSheet("#exchangeTree{font-size:14px;border:none;border-right: 1px solid rgba(50,50,50,100)}"
                           "#exchangeTree::item:hover{background-color:rgba(0,255,0,50)}"
                           "#exchangeTree::item:selected{background-color:rgba(255,0,0,100)}"
                           "#exchangeTree::item{height:28px;}"
                           )

    def mouseDoubleClickEvent(self, event):
        event.accept()

    def item_clicked(self, tree_item):
        if tree_item.childCount():
            if tree_item.isExpanded():
                tree_item.setExpanded(False)
                # tree_item.setIcon(0, QIcon("icons/arrow_right.png"))
            else:
                tree_item.setExpanded(True)
                # tree_item.setIcon(0, QIcon("icons/arrow_bottom.png"))
            self.unselected_signal.emit()
        elif tree_item.parent():
            item_id = getattr(tree_item, "id")
            parent_id = getattr(tree_item.parent(), "id")
            self.selected_signal.emit(parent_id, item_id)
