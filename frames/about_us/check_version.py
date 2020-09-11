# _*_ coding:utf-8 _*_
# @File  : check_version.py
# @Time  : 2020-09-11 10:19
# @Author: zizle
import os
import sys
import json
from subprocess import Popen
from PyQt5.QtWidgets import qApp
from PyQt5.QtCore import Qt, QUrl, QSettings
from PyQt5.QtNetwork import QNetworkRequest
from popup.message import InformationPopup
from settings import BASE_DIR, SYS_BIT, SERVER_API, PLATE_FORM, ADMINISTRATOR
from .check_version_ui import CheckVersionUI


class CheckVersion(CheckVersionUI):
    """ 版本检查 """
    def __init__(self, *args, **kwargs):
        super(CheckVersion, self).__init__(*args, **kwargs)
        self.is_last = True  # 是否是最新版本
        self.update_right_now.setEnabled(False)
        self.get_client_uuid()
        self._get_last_version()
        self.update_right_now.clicked.connect(self.exit_for_updating)

    def get_client_uuid(self):
        config_filepath = os.path.join(BASE_DIR, "dawn/client.ini")
        config = QSettings(config_filepath, QSettings.IniFormat)
        client_uuid = config.value("TOKEN/UUID") if config.value("TOKEN/UUID") else '未知'
        self.client_uuid.setText(client_uuid)

    def _get_last_version(self):
        """ 获取最新版本号 """
        # 获取当前版本号
        json_file = os.path.join(BASE_DIR, "classini/update_{}_{}.json".format(PLATE_FORM, SYS_BIT))
        if not os.path.exists(json_file):
            self.current_version.setText("检测失败.")
            self.last_version.setText("检测失败.")
            return

        with open(json_file, "r", encoding="utf-8") as jf:
            update_json = json.load(jf)

        self.current_version.setText(update_json["VERSION"])
        is_manager = 1 if ADMINISTRATOR else 0
        url = SERVER_API + "check_version/?version={}&plateform={}&sys_bit={}&is_manager={}".format(
            update_json["VERSION"], PLATE_FORM, SYS_BIT, is_manager)
        request = QNetworkRequest(QUrl(url))
        network_manager = getattr(qApp, "_network")
        reply = network_manager.get(request)
        reply.finished.connect(self.last_version_back)

    def last_version_back(self):
        """ 检测版本结果 """
        reply = self.sender()
        if reply.error():
            reply.deleteLater()
            self.last_version.setText("检测失败.")
            return
        data = reply.readAll().data()
        u_data = json.loads(data.decode("utf-8"))
        if u_data["update_needed"]:
            for_update_file = os.path.join(BASE_DIR, "classini/for_update_{}.json".format(SYS_BIT))
            # 写入待更新信息
            f_data = {
                "VERSION": u_data["last_version"],
                "SERVER": u_data["file_server"],
                "FILES": u_data["update_files"]
            }
            with open(for_update_file, "w", encoding="utf-8") as f:
                json.dump(f_data, f, indent=4, ensure_ascii=False)
            # 填写更新内容
            self.update_detail.setText(u_data["update_detail"])
            self.update_right_now.setEnabled(True)
        else:
            self.update_right_now.setText("无需更新")
        self.last_version.setText(u_data["last_version"])
        reply.deleteLater()

    def exit_for_updating(self):
        """ 退出当前程序，启动更新更新 """
        script_file = os.path.join(BASE_DIR, "AutoUpdate.exe")
        is_close = True
        if os.path.exists(script_file):
            try:
                Popen(script_file, shell=False)
            except OSError as e:
                self.run_message.setText(str(e))
                is_close = False
        else:
            p = InformationPopup("更新程序丢失...", self)
            p.exec_()
            is_close = False
        if is_close:
            sys.exit()
