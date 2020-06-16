# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-21
# ------------------------
"""32位系统更新程序"""

import os
import sys
import time
import json
from hashlib import md5 as hash_md5
from requests import get as request_get
from subprocess import Popen
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar
from PyQt5.QtGui import QPixmap, QFont, QPalette, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer

# HTTP_SERVER = "http://127.0.0.1:5000/"
HTTP_SERVER = "http://210.13.218.130:9002/"
ADMINISTRATOR = '1'
SYSTEM_BIT = "32"
APP_DAWN = QSettings('dawn/initial.ini', QSettings.IniFormat)

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


# 线程检测是否更新版本
class CheckUpdatingVersion(QThread):
    check_successful = pyqtSignal(dict)
    check_fail = pyqtSignal(bool)

    def run(self):
        version = APP_DAWN.value('VERSION')
        # print(version)
        if not version:
            version = ""
        identify = ADMINISTRATOR
        try:
            r = request_get(
                url=HTTP_SERVER + 'update/?identify=' + identify + '&version=' + str(version) + '&sbit=' + SYSTEM_BIT,
                headers={'User-Agent': 'RuiDa_ADSClient'}
            )
            if r.status_code != 200:
                raise ValueError('检测版本失败。')
            response = json.loads(r.content.decode('utf-8'))
        except Exception as e:
            self.check_fail.emit(True)
        else:
            self.check_successful.emit(response['data'])


# 线程下载新版本文件
class DownloadNewVersion(QThread):
    file_downloading = pyqtSignal(int, int, str)
    download_finished = pyqtSignal(bool)
    download_fail = pyqtSignal(str)

    def __init__(self, file_list, new_version, *args, **kwargs):
        super(DownloadNewVersion, self).__init__(*args, **kwargs)
        self.file_list = file_list
        self.file_count = len(file_list)
        self.update_file_list = dict()
        self.new_version = new_version
        self.download_process_error = False

    def run(self):
        # 获取本地文件
        self.find_local_files(BASE_DIR)
        # print(self.update_file_list)
        for index, file in enumerate(self.file_list):
            time.sleep(0.00000001)
            local_file_md5 = self.update_file_list.get(file, None)
            # print('文件名：',file, 'MD5：',local_file_md5)
            if local_file_md5 is not None:
                if local_file_md5 == self.file_list[file]:  # 对比MD5的值
                    # print('文件{}MD5相等, 无需下载。'.format(file))
                    self.file_downloading.emit(index, self.file_count, str(file))
                    continue
            #     else:
            #         print('文件存在,md5 不相等，需要下载文件')
            #         self.file_downloading.emit(index, self.file_count, str(file))
            #         self.download_file(file)
            #         time.sleep(0.000002)
            #         self.file_downloading.emit(index + 1, self.file_count, str(file))
            # else:
            #     # 文件不存在，需要下载文件
            #     print('文件不存在,需要下载')
            self.file_downloading.emit(index, self.file_count, str(file))
            try:
                self.download_file(file)
            except Exception as e:
                self.download_process_error = True
                self.download_fail.emit(str(e))
                break

            self.file_downloading.emit(index + 1, self.file_count, str(file))
        # 下载完成，写入新版本号
        if not self.download_process_error:
            APP_DAWN.setValue('VERSION', str(self.new_version))
            self.download_finished.emit(True)

    # 请求下载文件
    def download_file(self, file_name):
        file_path = os.path.join(BASE_DIR, file_name)
        # print('正准备下载文件', file_name)
        r = request_get(
            url=HTTP_SERVER + 'downloading/',
            headers={'User-Agent': 'RuiDa_ADSClient', 'Content-Type': 'application/json;charset=utf8'},
            data=json.dumps({'filename': file_name, 'identify': ADMINISTRATOR, 'sbit': '32'})
        )
        if r.status_code != 200:
            response = r.content.decode('utf-8')
            raise ValueError(response['message'])
        file_dir = os.path.split(file_path)[0]
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        file_name = open(file_path, 'wb')
        file_name.write(r.content)
        file_name.close()

    # 计算文件的MD5
    def get_file_md5(self, filename):
        if not os.path.isfile(filename):
            return
        myHash = hash_md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8096)
            if not b:
                break
            myHash.update(b)
        f.close()
        return myHash.hexdigest()

    # 查找本地文件清单，并获取MD5值
    def find_local_files(self, path):
        fsinfo = os.listdir(path)
        for fn in fsinfo:
            temp_path = os.path.join(path, fn)
            if not os.path.isdir(temp_path):
                # print(temp_path)
                file_md5 = self.get_file_md5(temp_path)
                fn = str(temp_path.replace(BASE_DIR + '\\', ''))
                # print(fn)
                fn = '/'.join(fn.split('\\'))
                self.update_file_list[fn] = file_md5
            else:
                self.find_local_files(temp_path)


class StartPage(QLabel):
    def __init__(self, *args, **kwargs):
        super(StartPage, self).__init__(*args, *kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('分析决策系统自动更新程序')
        self._pressed = False
        self._mouse_pos = None
        icon_path = os.path.join(BASE_DIR, "media/logo.png")
        pix_path = os.path.join(BASE_DIR, "media/start.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setPixmap(QPixmap(pix_path))
        self.red = QPalette()
        self.red.setColor(QPalette.WindowText, Qt.red)
        self.blue = QPalette()
        self.blue.setColor(QPalette.WindowText, Qt.blue)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.setFixedSize(660, 400)
        self.setScaledContents(True)
        self.setFont(font)
        self.show_text = QLabel("欢迎使用分析决策系统\n正在检查新版本...", self)
        self.show_text.setFont(font)
        self.show_text.setFixedSize(self.width(), self.height())
        self.show_text.setAlignment(Qt.AlignCenter)
        self.show_text.setPalette(self.red)
        self.count_down = QTimer()
        self.count_down.timeout.connect(self.count_down_timeout)
        self.count_down_count = 6
        self.update_process_bar = QProgressBar(self)
        self.update_process_bar.setGeometry(0, 280, 660, 20)
        self.update_process_bar.setObjectName('processBar')
        self.setStyleSheet("""
        #processBar{
            text-align:center;
            border: 1px solid #61B661;
            border-radius: 3px;
            background-color:none;
        }
        #processBar::chunk {
            background-color: #71C671;
            border-radius: 3px;
        }
        """)
        # layout.addLayout(self.show_text)
        # self.showMessage("欢迎使用分析决策系统\n正在检查新版本...", Qt.AlignCenter, Qt.blue)

    def mousePressEvent(self, event):
        super(StartPage, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        super(StartPage, self).mouseReleaseEvent(event)
        self._pressed = False
        self._mouse_pos = None

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._mouse_pos:
            self.move(self.mapToGlobal(event.pos() - self._mouse_pos))
        event.accept()

    # 启动检查版本
    def check_version(self):
        self.checking_thread = CheckUpdatingVersion()
        self.checking_thread.finished.connect(self.checking_thread.deleteLater)
        self.checking_thread.check_successful.connect(self.version_checked)
        self.checking_thread.check_fail.connect(self.version_check_error)
        self.checking_thread.start()

    def version_checked(self, result):
        # print('版本检测成功', result)
        if result['update']:
            self.show_text.setText("欢迎使用分析决策系统,正在准备更新\n检测到新版本{}".format(result['version']))
            # 线程下载文件到目录中
            self.downloading = DownloadNewVersion(result['file_list'], new_version=result['version'])
            self.downloading.finished.connect(self.downloading.deleteLater)
            self.downloading.file_downloading.connect(self.setProcessing)
            self.downloading.download_finished.connect(self.update_finished)
            self.downloading.download_fail.connect(self.update_fail)
            self.downloading.start()
        else:
            self.show_text.setText("欢迎使用分析决策系统\n当前已是最新版本!")
            self.show_text.setPalette(self.blue)
            self.update_finished()

    def version_check_error(self):
        # 版本检测失败
        self.show_text.setText("网络错误！请检查网络设置...\n系统将在{}秒后退出!".format(self.count_down_count))
        self.count_down.start(1000)

    def count_down_timeout(self):
        self.count_down_count -= 1
        if self.count_down_count <= 0:
            self.count_down_count = 6
            self.count_down.stop()
            sys.exit()
        self.show_text.setText("网络错误！请检查网络设置...\n系统将在{}秒后退出!".format(self.count_down_count))

    def setProcessing(self, current_index, total_count, file_name):
        # rate = (current_index / total_count) * 100
        # file_name = os.path.split(file_name)[1]
        self.update_process_bar.setMaximum(total_count)
        self.update_process_bar.setValue(current_index + 1)
        if current_index == total_count:
            self.show_text.setText("欢迎使用分析决策系统\n更新完成!")
        else:
            # self.show_text.setText("欢迎使用分析决策系统\n系统正在更新中...\n"+file_name+"\n{:.0f}%".format(rate))
            self.show_text.setText("欢迎使用分析决策系统\n系统正在更新中...")
        self.show_text.setPalette(self.blue)

    def update_fail(self, error):
        self.show_text.setText("系统更新失败...\n{}\n稍后将自动退出!".format(error))
        self.show_text.setPalette(self.red)
        QApplication.processEvents()
        time.sleep(5)
        self.close()
        sys.exit()

    def update_finished(self):
        # 更新完成，执行系统主程序DecisionClient.py
        if os.path.exists("Decision.exe"):
            Popen('Decision.exe', shell=False)
        self.close()
        sys.exit()


app = QApplication(sys.argv)
splash = StartPage()
splash.show()
app.processEvents()
splash.check_version()
sys.exit(app.exec_())
