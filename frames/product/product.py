# _*_ coding:utf-8 _*_
# @File  : product.py
# @Time  : 2020-09-15 11:01
# @Author: zizle
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from .product_ui import ProductUI
from .short_message import ShortMessage


class ProductPage(ProductUI):
    def __init__(self, *args, **kwargs):
        super(ProductPage, self).__init__(*args, **kwargs)
        # 添加左侧菜单
        menus = [
            {"menu_id": "1", "menu_name": "资讯服务", "children": [
                {"menu_id": "1_1", "menu_name": "短信通"},
                {"menu_id": "1_2", "menu_name": "市场分析"},
            ]}
        ]

        for menu_item in menus:
            head = self.menu_folded.addHead(menu_item["menu_name"])
            body = self.menu_folded.addBody(head=head)
            for children_item in menu_item["children"]:
                body.addButton(id=children_item["menu_id"], name=children_item["menu_name"], name_en=children_item["menu_name"])
        self.menu_folded.container.layout().addStretch()
        self.menu_folded.setBodyHorizationItemCount()

        self.menu_folded.left_mouse_clicked.connect(self.create_menu_tab)

    def create_menu_tab(self, menu_id, parent_text, menu_name):
        """ 进入功能页面 """
        if menu_id == "1_1":
            # 短信通页面
            tab = ShortMessage(self.frame_tab)
        else:
            tab = QLabel(
                "「" + menu_name + "」暂未开放···\n更多资讯请访问【首页】查看.",
                styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                alignment=Qt.AlignCenter)
        self.frame_tab.setCentralWidget(tab)



