# _*_ coding:utf-8 _*_
# @File  : homepage_b.py
# @Time  : 2020-07-19 15:14
# @Author: zizle
import webbrowser
import json
from PyQt5.QtWidgets import qApp, QListWidgetItem
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QUrl, QEventLoop, pyqtSignal, Qt
from PyQt5.QtNetwork import QNetworkRequest
from widgets.pdf_shower import PDFContentPopup
from popup.advertisement import TextPopup
from popup.spot_price import SpotPricePopup
from .homepage_ui import HomepageUI, ControlButton, PixMapLabel, LeftChildrenMenuWidget
from settings import SERVER_API, STATIC_URL, HOMEPAGE_MENUS


class Homepage(HomepageUI):
    """ 首页业务 """
    SkipPage = pyqtSignal(str, str)

    def __init__(self, *args, **kwargs):
        super(Homepage, self).__init__(*args, **kwargs)
        self.event_loop = QEventLoop(self)
        # 滚动条的滚动移动相对于父窗口的控制button位置
        self.horizontalScrollBar().valueChanged.connect(self.horizontal_scroll_value_changed)
        self.verticalScrollBar().valueChanged.connect(self.vertical_scroll_value_changed)

        """ 左侧菜单及显示业务 """
        self.add_left_menus()
        self.left_menu.currentRowChanged.connect(self.left_menu_selected)

        """ 右侧广告及其他相关业务 """
        self.control_buttons = list()
        self.get_all_advertisement()
        # self.slide_stacked.autoStart(msec=4000)  # 自动开启得放置于填充图片之后,否则闪退
        self.slide_stacked.clicked_release.connect(self.image_widget_clicked)
        self.slide_stacked.currentChanged.connect(self.change_button_icon)  # 图片变化设置icon的背景

        # 获取即时资讯板块初始化信息
        self.get_instant_message()
        # 即时通讯内容表格的点击事件
        self.instant_message_widget.content_table.cellClicked.connect(self.view_detail_instant_message)
        # 点击更多短信通
        self.instant_message_widget.more_button.clicked.connect(self.view_more_instant_message)

        # 获取现货报价板块初始化信息
        self.get_latest_spot_price()
        # 点击了现货报价的更多
        self.spot_price_widget.more_button.clicked.connect(self.more_sport_price_popup)

        # 获取每日收盘报告
        self.get_latest_daily_report()
        # 每日报告内容表格的点击事件
        self.daily_report_widget.content_table.cellClicked.connect(self.view_detail_daily_report)
        # 每日收盘评论点击更多
        self.daily_report_widget.more_button.clicked.connect(self.view_more_daily_report)

        # 获取周度报告
        self.get_latest_weekly_report()
        # 周度报告的内容表格点击事件
        self.weekly_report_widget.content_table.cellClicked.connect(self.view_detail_weekly_report)
        # 周度报告评论点击更多
        self.weekly_report_widget.more_button.clicked.connect(self.view_more_weekly_report)

        # 获取月季报告
        self.get_latest_monthly_report()
        # 月季报告的内容表格点击事件
        self.monthly_report_widget.content_table.cellClicked.connect(self.view_detail_monthly_report)
        # 周度报告评论点击更多
        self.monthly_report_widget.more_button.clicked.connect(self.view_more_monthly_report)

        # 获取年度报告
        self.get_latest_annual_report()
        # 月季报告的内容表格点击事件
        self.annual_report_widget.content_table.cellClicked.connect(self.view_annual_monthly_report)
        # 周度报告评论点击更多
        self.annual_report_widget.more_button.clicked.connect(self.view_more_annual_report)

    def add_left_menus(self):
        """ 添加左侧菜单列表 """
        # 遍历菜单,增加QListWidgetItem和新增stackedWidget
        for list_menu in HOMEPAGE_MENUS:
            menu_item = QListWidgetItem(list_menu["name"])
            self.left_menu.addItem(menu_item)
            left_widget = LeftChildrenMenuWidget(list_menu["children"], self)
            left_widget.SelectedMenu.connect(self.left_children_menu_selected)
            self.left_stacked.addWidget(left_widget)
        item = self.left_menu.item(0)
        item.setSelected(True)

    def left_menu_selected(self, row):
        """ 点击了左侧的listItem """
        self.left_stacked.setCurrentIndex(row)

    def left_children_menu_selected(self, menu_id, menu_text):
        """ 点击左侧的子菜单 """
        print(menu_id, menu_text)
        # 处理菜单能在本页面完成的在本页面,如不能在本页面完成的,传出信号到主窗口去跳转

        self.SkipPage.emit(menu_id, menu_text)

    def horizontal_scroll_value_changed(self, value):
        """ 横向滚动条滚动事件 """
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE - value, 0 - self.verticalScrollBar().value())  # 移动控制控件

    def vertical_scroll_value_changed(self, value):
        """ 纵向滚动条滚动事件 """
        self.control_widget.move(self.CONTROL_LEFT_DISTANCE - self.horizontalScrollBar().value(), 0 - value)

    def get_all_advertisement(self):
        """ 获取所有的广告信息 """
        url = SERVER_API + 'advertisement/'
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.get_advertisement_reply)
        self.event_loop.exec_()

    def get_advertisement_reply(self):
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            self.show_advertisement(data["advertisements"])
            self.event_loop.quit()  # 没使用同步无法加载出控制的按钮
        reply.deleteLater()

    def show_advertisement(self, advertisements):
        """ 显示所有的广告"""
        self.control_buttons.clear()
        for index, ad_item in enumerate(advertisements):
            label = PixMapLabel(ad_item, self.slide_stacked)  # 内置QThread访问图片
            self.slide_stacked.addWidget(label)
            button = ControlButton("media/icons/empty_circle.png", "media/icons/full_circle.png", self.control_widget)
            if index == 0:
                button.setIcon(QIcon(button.hover_icon_path))
            setattr(button, "image_index", index)
            button.clicked.connect(self.skip_to_image)
            self.control_buttons.append(button)
            self.control_widget.layout().addWidget(button)
        if advertisements:
            self.slide_stacked.autoStart(msec=4000)

    # def add_images(self):
    #     """ 添加轮播的图片信息（开发GUI测试代码） """
    #     # 获取广告信息
    #     self.control_buttons.clear()
    #     for index, name in enumerate(os.listdir('Data/Images')):
    #         label = QLabel(self.slide_stacked)
    #         label.setScaledContents(True)
    #         label.setPixmap(QPixmap('Data/Images/' + name))
    #         self.slide_stacked.addWidget(label)
    #         button = ControlButton("media/icons/empty_circle.png", "media/icons/full_circle.png", self.control_widget)
    #         if index == 0:
    #             button.setIcon(QIcon(button.hover_icon_path))
    #         setattr(button, "image_index", index)
    #         button.clicked.connect(self.skip_to_image)
    #         self.control_buttons.append(button)
    #         self.control_widget.layout().addWidget(button)

    def change_button_icon(self, current_index):
        """ 改变button的背景icon """
        for button in self.control_buttons:
            if getattr(button, "image_index") == current_index:
                button.setIcon(QIcon(button.hover_icon_path))
            else:
                button.setIcon(QIcon(button.icon_path))

    def image_widget_clicked(self):
        """ 点击了广告 """
        current_ad = self.slide_stacked.currentWidget()
        ad_data = current_ad.get_ad_data()
        # 根据ad_data显示出来广告响应
        ad_type = ad_data["ad_type"]
        if ad_type == "file":
            file_url = STATIC_URL + ad_data["filepath"]
            p = PDFContentPopup(file=file_url, title=ad_data["title"])
            p.exec_()
        elif ad_type == "web":
            webbrowser.open_new_tab(ad_data["web_url"])
        elif ad_type == "content":
            p = TextPopup(message=ad_data["content"])
            p.setWindowTitle(ad_data["title"])
            p.exec_()
        else:
            pass

    def skip_to_image(self):
        """ 跳到指定广告 """
        target_index = getattr(self.sender(), "image_index")
        if target_index is not None:
            self.slide_stacked.setCurrentIndex(target_index)
            self.change_button_icon(target_index)

    def get_instant_message(self):
        """ 获取即时资讯(短信通) """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "instant-message/?count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.instant_message_reply)

    def instant_message_reply(self):
        """ 即时资讯返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.instant_message_widget.set_contents(
                content_values=data["short_messages"], content_keys=["content", "time_str"],
                data_keys=["create_time"], resize_cols=[1], column_text_color={1: QColor(100,100,100)},
                zero_text_color=[], center_alignment_columns=[]
            )
        reply.deleteLater()

    def view_detail_instant_message(self, row, col):
        """ 查看详细的即时信息 """
        if col == 0:
            item = self.instant_message_widget.content_table.item(row, col)
            create_time = item.data(Qt.UserRole).get("create_time", "未知时间")
            create_time = create_time.replace("T", " ")[:16]
            text = "<div style='text-indent:30px;line-height:25px;font-size:13px;'>" \
                    "<span style='font-size:15px;font-weight:bold;color:rgb(233,20,20);'>{}</span>" \
                    "{}</div>".format(create_time, item.text())
            p = TextPopup(text, self)
            p.setWindowTitle("即时资讯")
            p.resize(550, 180)
            p.exec_()

    def get_latest_spot_price(self):
        """ 获取最新现货报价 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "latest-spotprice/?count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_spot_price_reply)

    def latest_spot_price_reply(self):
        """ 最新现货报价数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.spot_price_widget.set_contents(
                content_values=data["sport_prices"], content_keys=["variety_zh", "spot_price", "price_increase", "date"],
                data_keys=[], resize_cols=[3], column_text_color={3: QColor(100, 100, 100)},
                zero_text_color=[2], center_alignment_columns=[1, 2]
            )
        reply.deleteLater()

    def more_sport_price_popup(self):
        """ 显示更多现货报价的信息 """
        p = SpotPricePopup(self)
        p.exec_()

    def get_latest_daily_report(self):
        """ 获取最新日报信息 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "latest-report/?report_type=daily&count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_daily_report_reply)

    def latest_daily_report_reply(self):
        """ 最新日常报告数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.daily_report_widget.set_contents(
                content_values=data["reports"],
                content_keys=["title", "date"],
                data_keys=["filepath"], resize_cols=[1], column_text_color={1: QColor(100, 100, 100)},
                zero_text_color=[], center_alignment_columns=[]
            )
        reply.deleteLater()

    def view_detail_daily_report(self, row, col):
        """ 查看报告的详细内容 """
        if col == 0:
            item = self.daily_report_widget.content_table.item(row, col)
            title = item.text()
            file_url = STATIC_URL + item.data(Qt.UserRole).get("filepath", 'no-found.pdf')
            p = PDFContentPopup(file=file_url, title=title)
            p.exec_()

    def view_more_daily_report(self):
        """ 查看更多的日常报告 """
        self.SkipPage.emit("l_0_0", "收盘日评")

    def view_more_weekly_report(self):
        """ 查看更多的周报 """
        self.SkipPage.emit("l_0_1", "周度报告")

    def view_more_monthly_report(self):
        """ 查看更多的周报 """
        self.SkipPage.emit("l_0_2", "月季报告")

    def view_more_annual_report(self):
        """ 查看更多的年度报 """
        self.SkipPage.emit("l_0_3", "年度报告")

    def view_more_instant_message(self):
        """ 查看更多的年度报 """
        self.SkipPage.emit("l_1_0", "短信通")

    def get_latest_weekly_report(self):
        """ 获取最新周报信息 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "latest-report/?report_type=weekly&count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_weekly_report_reply)

    def latest_weekly_report_reply(self):
        """ 最新周度报告数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.weekly_report_widget.set_contents(
                content_values=data["reports"],
                content_keys=["title", "date"],
                data_keys=["filepath"], resize_cols=[1], column_text_color={1: QColor(100, 100, 100)},
                zero_text_color=[], center_alignment_columns=[]
            )
        reply.deleteLater()

    def view_detail_weekly_report(self, row, col):
        """ 查看周度报告的详细内容 """
        if col == 0:
            item = self.weekly_report_widget.content_table.item(row, col)
            title = item.text()
            file_url = STATIC_URL + item.data(Qt.UserRole).get("filepath", 'no-found.pdf')
            p = PDFContentPopup(file=file_url, title=title)
            p.exec_()

    def get_latest_monthly_report(self):
        """ 获取最新月报信息 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "latest-report/?report_type=monthly&count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_monthly_report_reply)

    def latest_monthly_report_reply(self):
        """ 最新月季报告数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.monthly_report_widget.set_contents(
                content_values=data["reports"],
                content_keys=["title", "date"],
                data_keys=["filepath"], resize_cols=[1], column_text_color={1: QColor(100, 100, 100)},
                zero_text_color=[], center_alignment_columns=[]
            )
        reply.deleteLater()

    def view_detail_monthly_report(self, row, col):
        """ 查看月度报告的详细内容 """
        if col == 0:
            item = self.monthly_report_widget.content_table.item(row, col)
            title = item.text()
            file_url = STATIC_URL + item.data(Qt.UserRole).get("filepath", 'no-found.pdf')
            p = PDFContentPopup(file=file_url, title=title)
            p.exec_()

    def get_latest_annual_report(self):
        """ 获取最新年报半年报信息 """
        network_manager = getattr(qApp, "_network")
        url = SERVER_API + "latest-report/?report_type=annual&count=8"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.latest_annual_report_reply)

    def latest_annual_report_reply(self):
        """ 最新年报半年报数据返回 """
        reply = self.sender()
        if reply.error():
            pass
        else:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            # 将数据进行展示
            self.annual_report_widget.set_contents(
                content_values=data["reports"],
                content_keys=["title", "date"],
                data_keys=["filepath"], resize_cols=[1], column_text_color={1: QColor(100, 100, 100)},
                zero_text_color=[], center_alignment_columns=[]
            )
        reply.deleteLater()

    def view_annual_monthly_report(self, row, col):
        """ 查看年报半年报的详细内容 """
        if col == 0:
            item = self.annual_report_widget.content_table.item(row, col)
            title = item.text()
            file_url = STATIC_URL + item.data(Qt.UserRole).get("filepath", 'no-found.pdf')
            p = PDFContentPopup(file=file_url, title=title)
            p.exec_()

