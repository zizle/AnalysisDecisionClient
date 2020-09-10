# _*_ coding:utf-8 _*_
# @File  : client_manager.py
# @Time  : 2020-09-10 17:48
# @Author: zizle
from .client_manager_ui import ClientManageUI

class ClientManage(ClientManageUI):
    def __init__(self, *args, **kwargs):
        super(ClientManage, self).__init__(*args, **kwargs)
