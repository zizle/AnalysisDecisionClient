# _*_ coding:utf-8 _*_
# @File  : AutoUpdate.py
# @Time  : 2020-08-03 10:51
# @Author: zizle

""" 版本更新程序 """

import os
import sys
import json
import time
import logging
import requests
from subprocess import Popen
from PyQt5.QtWidgets import QApplication, QProgressBar, QLabel, QPushButton
from PyQt5.QtCore import Qt, QUrl, QFile, QSize, QThread, pyqtSignal
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QFont, QImage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATEFORM = "WIN7"

""" 日志配置 """


def config_logger_handler():
    # 日志配置
    log_folder = os.path.join(BASE_DIR, "logs/")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_file_name = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_path = log_folder + os.sep + log_file_name

    handler = logging.FileHandler(log_file_path, encoding='UTF-8')
    handler.setLevel(logging.ERROR)
    # "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s[line:%(lineno)d]"
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s : %(message)s"
    )
    handler.setFormatter(logger_format)
    return handler


logger = logging.getLogger('errorlog')
logger.addHandler(config_logger_handler())


class DownloadFileThread(QThread):
    """ 线程下载文件"""
    file_download_finished = pyqtSignal(int)
    download_fail = pyqtSignal()

    def __init__(self, url_list, *args, **kwargs):
        super(DownloadFileThread, self).__init__(*args, **kwargs)
        self.sys_bit = "32" if sys.maxsize < 2 ** 32 else "64"
        self.url_list = url_list

    def run(self):
        for index, request_url in enumerate(self.url_list):
            # 下载文件
            is_download = self.download_file(request_url)
            if not is_download:
                self.download_fail.emit()
                break
            # 发出当前的索引+1
            self.file_download_finished.emit(index + 1)

    def download_file(self, url):
        """ 下载文件 """
        split_ = url.split("/{}/".format(self.sys_bit))
        save_file_path = os.path.join(BASE_DIR, split_[1])
        # 文件夹不存在创建
        save_dir = os.path.split(save_file_path)[0]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        try:
            r = requests.get(url, headers={"User-Agent": "FAClientUp"})
            if r.status_code != 200:
                raise ValueError("Status Code != 200")
            with open(save_file_path, "wb") as fp:
                fp.write(r.content)
        except Exception as e:
            logger.error("下载文件{}出错了:\n{}".format(split_[1], e))
            return False
        else:
            return True


class UpdatePage(QLabel):
    def __init__(self, *args, **kwargs):
        super(UpdatePage, self).__init__(*args, *kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('系统自动更新程序')
        self.url_stack = list()
        self.downloading_thread = None
        self.update_error = False
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
        self.show_text = QLabel("系统正在下载新版本文件...\n请勿退出...", self)
        self.show_text.setFont(font)
        self.show_text.setFixedSize(self.width(), self.height())
        self.show_text.setAlignment(Qt.AlignCenter)
        self.show_text.setPalette(self.blue)
        self.update_process_bar = QProgressBar(self)
        self.update_process_bar.setGeometry(1, 160, 498, 12)
        self.update_process_bar.setObjectName('processBar')
        font = QFont()
        font.setPointSize(8)
        font.setFamily('Webdings')
        self.force_exit = QPushButton('r', self)
        self.force_exit.setFont(font)
        self.force_exit.setGeometry(478, 3, 18, 18)
        self.force_exit.setObjectName("forceBtn")
        self.force_exit.clicked.connect(self.user_force_exit)
        self.setStyleSheet("""
        #forceBtn{
            border:none;color:rgb(100,100,100)
        }
        #forceBtn:hover{color:rgb(233,66,66)}
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

    def user_force_exit(self):
        logger.error("用户在更新中强制退出!")
        self.close()
        sys.exit(0)

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
        self.url_stack.clear()
        for file_path, file_hash in for_update_dict.items():
            old_hash = old_dict.get(file_path, None)
            if old_hash is not None and old_hash == file_hash:
                continue
            # 生成请求文件的url,放入待更新的列表中
            url = self._server + "{}/{}/{}".format(PLATEFORM, self.sys_bit, file_path)
            self.url_stack.append(url)
        self.update_process_bar.setMaximum(len(self.url_stack))
        self.exec_downloading()  # 开启线程执行下载

    def exec_downloading(self):
        """ 开始文件下载 """
        if self.downloading_thread is not None:
            self.downloading_thread = None
        self.downloading_thread = DownloadFileThread(url_list=self.url_stack)
        self.downloading_thread.file_download_finished.connect(self.update_process_bar.setValue)
        self.downloading_thread.download_fail.connect(self.downloading_file_fail)
        self.downloading_thread.finished.connect(self.update_finished)
        self.downloading_thread.start()

    def downloading_file_fail(self):
        """ 下载文件失败 """
        self.update_error = True
        self.update_process_bar.setValue(len(self.url_stack))

    def update_finished(self):
        """ 更新结束 """
        if self.update_error:  # 更新失败
            self.show_text.setText("更新失败\n具体信息查看日志!")
            self.show_text.setPalette(self.red)
        else:
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


app = QApplication([])
updater = UpdatePage()
updater.show()
sys.exit(app.exec_())
