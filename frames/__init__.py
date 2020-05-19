# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------

import os
import json
import time
import pickle
import shutil
import requests
from PyQt5.QtWidgets import QLabel, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QSize

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
        # 请求启动页
        try:
            r = requests.get(url=settings.STATIC_PREFIX + 'startpng/start.png')
            response_img = r.content
            if r.status_code != 200:
                raise ValueError('get starting image error')
            start_image = QImage.fromData(response_img)
        except Exception:
            pixmap = QPixmap('media/start.png')
        else:
            pixmap = QPixmap.fromImage(start_image)
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
            time.sleep(1.5)
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
        import pandas


# 主窗口(无边框)
class ADSClient(FrameLessWindow):

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
                # print(response)
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
            avatar_url = settings.SERVER_ADDR[:-1] + response_data['avatar']
            self.navigation_bar.permit_bar.setAvatar(avatar_url)
        # 改变显示用户名
        self.navigation_bar.permit_bar.show_username(dynamic_username)

        # 设置用户id
        self.navigation_bar.permit_bar.set_user_id(response_data['id'])
        # 菜单
        modules = self.get_system_modules()
        self.navigation_bar.module_bar.setMenus(modules)

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
    def user_register_success(self, userinfo):
        # 再发起登录
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'login/',
                headers={'Content-Type': "application/json;charset=utf-8"},
                data=json.dumps({
                    "username": userinfo['username'],
                    "phone": userinfo["phone"],
                    "password": userinfo["password"],
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
        try:
            page = UserCenter(user_id, parent=self.page_container)
            page.avatar_changed.connect(self.navigation_bar.permit_bar.setAvatar)
            page.psd_changed.connect(self.navigation_bar.permit_bar.user_logout)
            self.page_container.addWidget(page)
        except Exception as e:
            print(e)

    # 检测是否有权限进入
    def is_accessed_module(self, module_id):
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'module/' + str(module_id) + '/',
                headers={'Content-Type': "application/json;charset=utf8"},
                data=json.dumps({"utoken": settings.app_dawn.value('AUTHORIZATION')})
            )
            response = json.loads(r.content.decode('utf-8'))
            if not response['auth']:
                raise ValueError("您还没开通这个功能,联系管理员开通。")
        except Exception as e:
            # 弹窗提示
            info_popup = InformationPopup(parent=self, message=str(e))
            info_popup.exec_()
            return False
        else:  # 模块权限验证通过
            return True

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
        else:
            page = QLabel(parent=self.page_container,
                          styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                          alignment=Qt.AlignCenter)
            page.setText("「" + module_text + "」还不能进行后台管理\n正在加紧开发中~.")
        return page

    # 进入功能页面,含后台的运营管理
    def to_module_page(self, module_text):
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
        elif module_text == '基本分析':
            from frames.basetrend import TrendPage
            page = TrendPage()
            page.getGroupVarieties()
        elif module_text == '计算平台':
            from frames.formulas import FormulasCalculate
            page = FormulasCalculate()
            page.getGroupVarieties()
        else:
            page = QLabel(parent=self.page_container,
                          styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                          alignment=Qt.AlignCenter)
            page.setText("「" + module_text + "」暂未开放\n敬请期待,感谢支持~.")
        return page

    # 点击模块菜单事件(接受到模块的id和模块名称)
    def module_clicked(self, module_id, module_text):
        print(module_id, module_text)
        if module_id == -9:
            page = self.to_data_manage_page(module_text)
        else:
            if not self.is_accessed_module(module_id):
                page = QLabel(parent=self.page_container,
                              styleSheet='font-size:16px;font-weight:bold;color:rgb(230,50,50)',
                              alignment=Qt.AlignCenter)
                page.setText("您还没有进入「" + module_text + "」的权限...\n请联系管理员进行开通.")
            else:
                page = self.to_module_page(module_text)
        self.page_container.clear()
        self.page_container.addWidget(page)
