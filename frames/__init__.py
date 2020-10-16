# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------


from .frameless import ClientMainApp
from utils.client import get_client_uuid
from settings import ADMINISTRATOR, SERVER_API, STATIC_URL, BASE_DIR, logger
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import qApp, QSplashScreen, QLabel
import os
import sys
import json
import time
import pickle
import shutil
import requests
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from frames.homepage import Homepage
from utils.machine import get_machine_code
from popup import InformationPopup
from popup.login import LoginPopup
from popup.register import RegisterPopup
from .frame_less import FrameLessWindow
from .ucenter import UserCenter
import settings

""" 欢迎页 """


class WelcomePage(QSplashScreen):
    def __init__(self, *args, **kwargs):
        super(WelcomePage, self).__init__(*args, *kwargs)
        self._bind_global_network_manager()                  # 绑定全局网络管理器

        self._get_start_image()                              # 获取开启的图片

        self._add_client_to_server()                         # 添加客户端到服务器

    def _bind_global_network_manager(self):
        """ 绑定全局网络管理器 """
        if not hasattr(qApp, "_network"):
            network_manager = QNetworkAccessManager(self)
            setattr(qApp, "_network", network_manager)

    def _add_client_to_server(self):
        """ 新增客户端 """
        client_uuid = get_client_uuid()
        if not client_uuid:
            logger.error("GET CLIENT-UUID FAIL.")
            self.close()
            sys.exit(-1)

        client_info = {
            'client_name': '',
            'machine_uuid': client_uuid,
            'is_manager': ADMINISTRATOR
        }
        network_manager = getattr(qApp, '_network')
        url = SERVER_API + "client/"
        reply = network_manager.post(QNetworkRequest(QUrl(url)), json.dumps(client_info).encode('utf-8'))
        reply.finished.connect(self.add_client_reply)

    def add_client_reply(self):
        """ 添加客户端的信息返回了 """
        reply = self.sender()
        if reply.error():
            logger.error("New Client ERROR!{}".format(reply.error()))
            sys.exit(-1)
        data = reply.readAll().data()
        data = json.loads(data.decode("utf-8"))
        reply.deleteLater()
        # 将信息写入token
        client_uuid = data["client_uuid"]
        client_ini_path = os.path.join(BASE_DIR, "dawn/client.ini")
        token_config = QSettings(client_ini_path, QSettings.IniFormat)
        token_config.setValue("TOKEN/UUID", client_uuid)

    def _get_start_image(self):
        """ 获取开启的页面图片 """
        network_manager = getattr(qApp, "_network")
        url = STATIC_URL + "start_image_bg.png"
        reply = network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(self.start_image_reply)

    def start_image_reply(self):
        """ 开启图片返回 """
        reply = self.sender()
        if reply.error():
            pixmap = QPixmap('media/start.png')
        else:
            start_image = QImage.fromData(reply.readAll().data())
            pixmap = QPixmap(start_image)
        reply.deleteLater()
        scaled_map = pixmap.scaled(QSize(660, 400), Qt.KeepAspectRatio)
        self.setPixmap(scaled_map)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.setFont(font)
        self.showMessage("欢迎使用分析决策系统\n程序正在启动中...", Qt.AlignCenter, Qt.blue)

    # 启动使客户端存在
    def make_client_existed(self):
        machine_code = get_machine_code()  # 获取机器码
        # 查询机器是否存在
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'client/',
                timeout=(2, 5),
                headers={'Content-Type': 'application/json; charset=utf-8'},
                data=json.dumps({
                    'machine_code': machine_code,
                    'is_manager': settings.ADMINISTRATOR
                }),
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            settings.app_dawn.remove('machine')
            self.showMessage("欢迎使用分析决策系统\n获取数据失败...\n" + str(e), Qt.AlignCenter, Qt.red)
            QMessageBox.information(self, '错误', '连接服务器失败!')
            sys.exit(0)
        else:
            # 写入配置
            settings.app_dawn.setValue('machine', response['machine_code'])

    # 启动访问广告图片文件并保存至本地
    def getCurrentAdvertisements(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'ad/',
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            pass
        else:
            # 判断是否有slider文件夹
            slider_folder = os.path.join(settings.BASE_DIR, 'media/slider/')
            if os.path.exists(slider_folder):
                # 删除slider文件夹
                shutil.rmtree(slider_folder)
            os.makedirs(slider_folder)  # 创建文件夹
            # 遍历请求每一个图片
            for ad_item in response['adments']:
                file_name = ad_item['file_url'].rsplit('/', 1)[1]
                file_name = file_name.rsplit('.', 1)[0]
                image_name = ad_item['image_url'].rsplit('/', 1)[1]
                image_suffix = image_name.rsplit('.', 1)[1]
                image_name = file_name + '.' + image_suffix  # 用文件名保存后续可直接访问文件
                time.sleep(0.0001)
                r = requests.get(url=settings.STATIC_PREFIX + ad_item['image_url'])
                with open('media/slider/' + image_name, 'wb') as img:
                    img.write(r.content)

    # 导入模块到运行环境
    def import_packages(self):
        pass


# 主窗口(无边框)
class ADSClient(FrameLessWindow):

    # 绑定全局网络管理器
    def bind_network_manager(self):
        if not hasattr(qApp, "_network"):
            network_manager = QNetworkAccessManager(self)
            setattr(qApp, "_network", network_manager)

    def set_default_homepage(self):
        """ 设置默认首页 """
        self.page_container.clear()
        page = HomePage()
        page.getCurrentNews()
        page.getCurrentSliderAdvertisement()
        page.getFoldedBoxContent()
        page.folded_box_clicked(category_id=1, head_text='常规报告')  # 默认点击常规报告分类id=1
        self.page_container.addWidget(page)

    # 用户点击【登录】
    def user_to_login(self):
        login_popup = LoginPopup(parent=self)
        login_popup.user_listed.connect(self.user_login_successfully)
        if not login_popup.exec_():
            login_popup.deleteLater()
            del login_popup

    # 启动自动登录
    def running_auto_login(self):
        if settings.app_dawn.value('auto') == '1':  # 自动登录
            token = settings.app_dawn.value('AUTHORIZATION')
            if not token:
                self.user_to_login()
                return
            try:
                r = requests.get(
                    url=settings.SERVER_ADDR + 'login/?utoken=' + token,
                )
                response = json.loads(r.content.decode('utf-8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception:
                settings.app_dawn.remove('AUTHORIZATION')  # 状态保持失败移除token
                self.user_to_login()
                return  # 自动登录失败
            else:
                if response['user_data']:
                    self.user_login_successfully(response['user_data'])

    # 用户登录成功(注册成功)
    def user_login_successfully(self, response_data):
        # 保存token
        token = response_data['utoken']
        settings.app_dawn.setValue('UROLE', pickle.dumps(response_data['role_num']))
        settings.app_dawn.setValue('UKEY', pickle.dumps(response_data['id']))
        # token的处理
        settings.app_dawn.setValue('AUTHORIZATION', token)
        # 组织滚动显示用户名
        dynamic_username = response_data['username']
        if not response_data['username']:
            phone = response_data['phone']
            dynamic_username = phone[0:3] + '****' + phone[7:11]
        # 设置头像
        if response_data['avatar']:
            avatar_url = settings.STATIC_PREFIX + response_data['avatar']
        else:
            avatar_url = 'media/avatar.png'
        self.navigation_bar.permit_bar.setAvatar(avatar_url)
        # 改变显示用户名
        self.navigation_bar.permit_bar.show_username(dynamic_username)

        # 设置用户id
        self.navigation_bar.permit_bar.set_user_id(response_data['id'])
        # 菜单
        # modules = self.get_system_modules()
        # self.navigation_bar.module_bar.setMenus(modules)

    # 请求菜单项
    def get_system_modules(self):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'module/',
                headers={'Content-Type':'application/json;charset=utf8'},
                data=json.dumps({
                    'utoken':settings.app_dawn.value("AUTHORIZATION"),
                    'machine_code':settings.app_dawn.value("machine")
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception as e:
            return []
        else:
            return response['modules']

    # 用户点击【注册】
    def user_to_register(self):
        register_popup = RegisterPopup(parent=self)
        register_popup.setAttribute(Qt.WA_DeleteOnClose)
        register_popup.user_registered.connect(self.user_register_success)
        register_popup.exec_()

    # 用户注册成功
    def user_register_success(self, account):
        # account是经加密后的数据
        # 再发起登录
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'login/',
                headers={'Content-Type': "application/json;charset=utf-8"},
                data=json.dumps({
                    "account": account,
                    "machine_code": settings.app_dawn.value('machine', '')
                })
            )
            response = json.loads(r.content.decode('utf8'))
            if r.status_code != 200:
                raise ValueError(response["message"])
        except Exception as e:
            tip = InformationPopup(title="提示", message=str(e))
            tip.exec_()
        else:
            self.user_login_successfully(response['user_data'])

    # 用户点击【注销】
    def user_to_logout(self):
        if self.navigation_bar.permit_bar.username_shown.isHidden():
            return
        # print('用户点击注销按钮生效')
        # 清除菜单
        self.navigation_bar.module_bar.clear()
        # 移除token
        settings.app_dawn.remove('AUTHORIZATION')
        self.navigation_bar.permit_bar.user_logout()  # 注销

    # 跳转个人中心
    def skip_to_usercenter(self, user_id):
        self.page_container.clear()
        page = UserCenter(user_id, parent=self.page_container)
        page.avatar_changed.connect(self.navigation_bar.permit_bar.setAvatar)
        page.psd_changed.connect(self.navigation_bar.permit_bar.user_logout)
        self.page_container.addWidget(page)

    # 进入数据管理页面
    def to_data_manage_page(self, module_text):
        if module_text == u"首页管理":
            from admin.homepage import HomePageAdmin
            page = HomePageAdmin()
            page.add_left_menus()
        elif module_text == u"产品服务":
            from admin.prosever import ProductServiceAdmin
            page = ProductServiceAdmin()
            page.add_left_tree_menus()
        elif module_text == u'基本分析':
            from admin.basetrend import BaseTrendAdmin
            page = BaseTrendAdmin()
            page.add_left_menus()
        elif module_text == u'交割服务':
            from admin.delivery import DeliveryInfoAdmin
            page = DeliveryInfoAdmin()
        else:
            page = QLabel(parent=self.page_container,
                          styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                          alignment=Qt.AlignCenter)
            page.setText("「" + module_text + "」还不能进行后台管理\n正在加紧开发中~.")
        return page

    # 检测是否有权限并拒绝或进入
    def accessed_module(self, module_id, module_text):
        if module_id == "0":
            self.set_default_homepage()
            return
        network_manager = getattr(qApp, '_network')
        url = settings.SERVER_ADDR + 'module_access/'
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json;charset=utf-8")
        body_data = {
            "module_id": module_id,
            "module_text": module_text,
            "utoken": settings.app_dawn.value("AUTHORIZATION"),
            "client": settings.app_dawn.value("machine")
        }
        reply = network_manager.post(request, json.dumps(body_data).encode("utf-8"))
        reply.finished.connect(self.access_module_reply)

    def access_module_reply(self):
        reply = self.sender()
        data = reply.readAll().data()
        if reply.error():
            page = QLabel(parent=self.page_container,
                          styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                          alignment=Qt.AlignCenter)
            page.setText("网络开小差了,检查网络设置!\n{}".format(reply.error()))
        else:
            data = json.loads(data.decode('utf-8'))
            if data["allow_in"]:
                # 进入相应模块
                page = self.get_module_page(data["module_id"], data["module_text"])
            else:
                page = QLabel(parent=self.page_container,
                              styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                              alignment=Qt.AlignCenter)
                page.setText(data["message"])
        reply.deleteLater()
        self.page_container.clear()
        self.page_container.addWidget(page)

    # 进入功能页面
    def get_module_page(self, module_id, module_text):
        print(module_id, module_text, "允许进入")
        page = QLabel()
        return page
        if module_text == u'运营管理':
            from admin.oprator import OperatorMaintain
            page = OperatorMaintain()
            page.addOperatorItem()  # 加入管理项目
        elif module_text == u'首页':
            from frames.homepage import HomePage
            page = HomePage()
            page.getCurrentNews()
            page.getCurrentSliderAdvertisement()
            page.getFoldedBoxContent()
            page.folded_box_clicked(category_id=1, head_text='常规报告')  # 默认点击常规报告分类id=1
        elif module_text == u'产品服务':
            from frames.prosever import InfoServicePage
            page = InfoServicePage()
            page.addServiceContents()
        elif module_text == u'基本分析':
            from frames.basetrend import TrendPage
            page = TrendPage()
            page.getGroupVarieties()
        elif module_text == u'计算平台':
            from frames.formulas import FormulasCalculate
            page = FormulasCalculate()
            page.getGroupVarieties()
        elif module_text == u"交割服务":
            from frames.delivery import DeliveryPage
            page = DeliveryPage(self.page_container)
            page.get_latest_discuss()
        elif module_text == u"交易所数据":
            from frames.industry.exchange_query import ExchangeQuery
            page = ExchangeQuery()
        elif module_text == u"品种净持仓":
            from frames.industry.net_position import NetPosition
            page = NetPosition()
        else:
            page = QLabel(parent=self.page_container,
                          styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                          alignment=Qt.AlignCenter)
            page.setText("「" + module_text + "」暂未开放\n敬请期待,感谢支持~.")
        return page


        #
        # try:
        #     r = requests.get(
        #         url=settings.SERVER_ADDR + 'module/' + str(module_id) + '/',
        #         headers={'Content-Type': "application/json;charset=utf8"},
        #         data=json.dumps({"utoken": settings.app_dawn.value('AUTHORIZATION')})
        #     )
        #     response = json.loads(r.content.decode('utf-8'))
        #     if not response['auth']:
        #         raise ValueError("您还没开通这个功能,联系管理员开通。")
        # except Exception as e:
        #     # 弹窗提示
        #     info_popup = InformationPopup(parent=self, message=str(e))
        #     info_popup.exec_()
        #     return False
        # else:  # 模块权限验证通过
        #     return True