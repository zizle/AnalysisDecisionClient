# _*_ coding:utf-8 _*_
# ---------------------------
# Python_Version 3.6.3
# Author: zizle
# Created: 2020-05-18
# ---------------------------
import sys
from PyQt5.QtWidgets import QApplication
import pandas
from PyQt5.QtWebEngineWidgets import QWebEngineView
from frames import WelcomePage, ClientMainApp

app = QApplication(sys.argv)
splash = WelcomePage()
splash.show()
app.processEvents()  # non-blocking

main_app = ClientMainApp()

main_app.show()


# base_window = ADSClient()  # main window
# base_window.set_default_homepage()
# base_window.bind_network_manager()
# base_window.running_auto_login()
# base_window.show()
# splash.finish(base_window)


splash.finish(main_app)
sys.exit(app.exec_())
