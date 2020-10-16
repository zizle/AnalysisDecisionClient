# _*_ coding:utf-8 _*_
# @File  : AutoUpdate.py
# @Time  : 2020-08-03 10:51
# @Author: zizle

""" 版本更新程序 """

import os
import sys
import json
from subprocess import Popen
from PyQt5.QtWidgets import QApplication, QProgressBar, QLabel
from PyQt5.QtCore import Qt, QUrl, QFile, QSize
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QFont, QImage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATEFORM = "WIN7"


class UpdatePage(QLabel):
    def __init__(self, *args, **kwargs):
        super(UpdatePage, self).__init__(*args, *kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('系统自动更新程序')
        self.request_stack = list()
        self.update_error = False
        self.current_count = 0
        self.update_count = 0
        self._pressed = False
        self._mouse_pos = None
        self.sys_bit = "32" if sys.maxsize < 2 ** 32 else "64"
        self._server = ""
        self.network_manager = QNetworkAccessManager(self)
        icon_path = os.path.join(BASE_DIR, "icons/app.png")
        self.setWindowIcon(QIcon(icon_path))
        self.red = QPalette()
        self.red.setColor(QPalette.WindowText, Qt.red)
        self.blue = QPalette()
        self.blue.setColor(QPalette.WindowText, Qt.blue)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.setFixedSize(500, 200)
        self.setScaledContents(True)
        self.setFont(font)
        self.show_text = QLabel("系统正在下载新版本文件...", self)
        self.show_text.setFont(font)
        self.show_text.setFixedSize(self.width(), self.height())
        self.show_text.setAlignment(Qt.AlignCenter)
        self.show_text.setPalette(self.blue)
        self.update_process_bar = QProgressBar(self)
        self.update_process_bar.setGeometry(1, 160, 498, 12)
        self.update_process_bar.setObjectName('processBar')
        self.setStyleSheet("""
        #processBar{
            text-align:center;
            font-size: 12px;
            font-weight:100;
            border: 1px solid #77d333;
            border-radius: 5px;
            background-color:none;
        }
        #processBar::chunk {
            background-color: #77d363;
            border-radius: 3px;
            margin:2px
        }
        """)
        self.setWindowIcon(QIcon("media/version_update.png"))
        self.get_update_bg()

        self._updating()

    def mousePressEvent(self, event):
        super(UpdatePage, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        super(UpdatePage, self).mouseReleaseEvent(event)
        self._pressed = False
        self._mouse_pos = None

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._mouse_pos:
            self.move(self.mapToGlobal(event.pos() - self._mouse_pos))
        event.accept()

    def get_update_bg(self):
        """ 获取更新时的背景图 """
        old_update_file = os.path.join(BASE_DIR, "classini/update_{}.json".format(self.sys_bit))
        if not os.path.exists(old_update_file):
            pixmap = QPixmap('media/update_bg.png')
            scaled_map = pixmap.scaled(QSize(500, 200), Qt.KeepAspectRatio)
            self.setPixmap(scaled_map)
        else:
            with open(old_update_file, "r", encoding="utf-8") as new_f:
                new_json = json.load(new_f)
            server = new_json["SERVER"]
            url = server + "update_image_bg.png"
            reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
            reply.finished.connect(self.start_image_reply)

    def start_image_reply(self):
        """ 开启图片返回 """
        reply = self.sender()
        if reply.error():
            pixmap = QPixmap('media/update_bg.png')
        else:
            start_image = QImage.fromData(reply.readAll().data())
            pixmap = QPixmap(start_image)
        reply.deleteLater()
        scaled_map = pixmap.scaled(QSize(500, 200), Qt.KeepAspectRatio)
        self.setPixmap(scaled_map)

    def _updating(self):
        """ 更新 """
        # 读取更新的文件信息
        new_update_file = os.path.join(BASE_DIR, "classini/for_update_{}.json".format(self.sys_bit))
        old_update_file = os.path.join(BASE_DIR, "classini/update_{}_{}.json".format(PLATEFORM, self.sys_bit))
        if not os.path.exists(new_update_file) or not os.path.exists(old_update_file):
            self.show_text.setText("更新信息文件丢失...")
            self.show_text.setPalette(self.red)
            return
        with open(new_update_file, "r", encoding="utf-8") as new_f:
            new_json = json.load(new_f)
        with open(old_update_file, "r", encoding="utf-8") as old_f:
            old_json = json.load(old_f)
        self._server = new_json["SERVER"]
        for_update_dict = new_json["FILES"]
        old_dict = old_json["FILES"]
        self.update_count = len(for_update_dict)
        self.update_process_bar.setMaximum(self.update_count)
        for file_path, file_hash in for_update_dict.items():
            old_hash = old_dict.get(file_path, None)
            if old_hash is not None and old_hash == file_hash:
                # print(file_path, "hash相等")
                self.current_count += 1
                self.update_process_bar.setValue(self.current_count)
                if self.current_count >= self.update_count:
                    self.update_finished_restart_app()
                continue
            # 生成请求对象
            self.generate_requests(file_path)

        # 执行下载
        self.exec_downloading()

    def received_file(self):
        """ 接收到文件 """
        reply = self.sender()
        # 从路径中解析要保存的位置
        request_url = reply.request().url().url()
        split_ = request_url.split("/{}/".format(self.sys_bit))
        save_file_path = os.path.join(BASE_DIR, split_[1])
        # 文件夹不存在创建
        save_dir = os.path.split(save_file_path)[0]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        file_data = reply.readAll()
        if reply.error():
            # print("更新错误", reply.error())
            self.update_error = True
        file_obj = QFile(save_file_path)
        is_open = file_obj.open(QFile.WriteOnly)
        if is_open:
            file_obj.write(file_data)
            file_obj.close()
        else:
            self.update_error = True
        self.current_count += 1
        self.update_process_bar.setValue(self.current_count)
        reply.deleteLater()
        if self.current_count >= self.update_count:
            self.update_finished_restart_app()

    def generate_requests(self, file_path):
        """ 生成请求对象 """
        # http://127.0.0.1:8000/static/UPDATE/WIN10/{INSIDE|OUTSIDE}/{32|64}/xxxx
        url = self._server + "{}/{}/{}".format(PLATEFORM, self.sys_bit, file_path)
        self.request_stack.append(QNetworkRequest(QUrl(url)))

    def exec_downloading(self):
        """ 开始文件下载 """
        for request_item in self.request_stack:
            reply = self.network_manager.get(request_item)
            reply.finished.connect(self.received_file)

    def update_finished_restart_app(self):
        self.show_text.setText("更新完成!")
        if not self.update_error:   # 下载完毕后且之间无发生过错误,将新文件内容复制到旧文件,真正完成更新
            new_update_file = os.path.join(BASE_DIR, "classini/for_update_{}.json".format(self.sys_bit))
            old_update_file = os.path.join(BASE_DIR, "classini/update_{}_{}.json".format(PLATEFORM, self.sys_bit))
            with open(new_update_file, "r", encoding="utf-8") as new_f:
                new_json = json.load(new_f)
            del new_json["SERVER"]
            with open(old_update_file, "w", encoding="utf-8") as old_f:
                json.dump(new_json, old_f, indent=4, ensure_ascii=False)
            os.remove(new_update_file)
        # 重新启动主程序
        script_path = os.path.join(BASE_DIR, "FAClient.exe")
        if os.path.exists(script_path):
            Popen(script_path, shell=False)
            self.close()
            sys.exit()
        else:
            self.show_text.setText("更新成功\n执行文件不存在!")
            self.show_text.setPalette(self.red)


app = QApplication([])
updater = UpdatePage()
updater.show()
sys.exit(app.exec_())
