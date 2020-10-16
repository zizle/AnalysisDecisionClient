# _*_ coding:utf-8 _*_
# @File  : passport_ui.py
# @Time  : 2020-08-28 16:07
# @Author: zizle
import uuid
from PyQt5.QtWidgets import QWidget, QStackedWidget, QGridLayout, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QSettings


# 图片验证码控件
class ImageCodeLabel(QLabel):
    refresh_image_code = pyqtSignal()

    # 生成uuid
    def generate_uuid(self):
        uid = str(uuid.uuid4())
        return ''.join(uid.split('-'))

    # 鼠标点击
    def mousePressEvent(self, event):
        self.refresh_image_code.emit()
        event.accept()


class LoginUI(QWidget):
    """ 登录页面 """

    def __init__(self, *args, **kwargs):
        super(LoginUI, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        # 手机
        phone_layout = QHBoxLayout()
        phone_label = QLabel(self)
        phone_label.setPixmap(QPixmap('media/passport_icon/phone.png'))
        phone_layout.addWidget(phone_label)
        self.phone_edit = QLineEdit(self)
        self.phone_edit.setPlaceholderText("手机号/用户号")
        phone_layout.addWidget(self.phone_edit)
        layout.addLayout(phone_layout)
        # 手机号错误提示框
        self.phone_error = QLabel(self)
        self.phone_error.setObjectName("phoneError")
        layout.addWidget(self.phone_error)

        # 密码
        psd_layout = QHBoxLayout()
        password_label = QLabel(self)
        password_label.setPixmap(QPixmap('media/passport_icon/password.png'))
        psd_layout.addWidget(password_label)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("输入密码")
        psd_layout.addWidget(self.password_edit)
        layout.addLayout(psd_layout)
        # 密码错误提示框
        self.password_error = QLabel(self)
        self.password_error.setObjectName("psdError")
        layout.addWidget(self.password_error)

        # 验证码
        verify_layout = QHBoxLayout()
        image_code_label = QLabel(self)
        image_code_label.setPixmap(QPixmap('media/passport_icon/yanzheng.png'))
        image_code_label.setScaledContents(True)
        verify_layout.addWidget(image_code_label)
        self.image_code_edit = QLineEdit(self)
        self.image_code_edit.setPlaceholderText('填写右侧验证码')
        self.image_code_edit.setFixedHeight(35)
        verify_layout.addWidget(self.image_code_edit)
        self.image_code_show = ImageCodeLabel("获取验证码···", self)
        self.image_code_show.setMaximumSize(80, 36)
        verify_layout.addWidget(self.image_code_show)
        layout.addLayout(verify_layout)

        layout.addWidget(QLabel(self))  # 占位撑开布局

        # 记住密码
        remember_layout = QHBoxLayout(spacing=2)
        self.remember_psd = QCheckBox('记住密码')
        remember_layout.addWidget(self.remember_psd)
        # 记住登录
        self.remember_login = QCheckBox('自动登录')
        remember_layout.addWidget(self.remember_login)
        remember_layout.addStretch()
        layout.addLayout(remember_layout)
        # 登录错误框
        self.login_error = QLabel(self)
        self.login_error.setObjectName("loginError")
        layout.addWidget(self.login_error)
        # 确认登录
        confirm_layout = QHBoxLayout()
        self.to_register_button = QPushButton("还没账户,立即注册->", self)
        confirm_layout.addWidget(self.to_register_button)
        confirm_layout.addStretch()
        self.login_button = QPushButton('登录 ', self)
        self.login_button.setObjectName("loginBtn")
        self.login_button.setMinimumWidth(200)
        confirm_layout.addWidget(self.login_button)
        layout.addLayout(confirm_layout)

        phone_label.setFixedSize(36, 35)
        phone_label.setScaledContents(True)
        self.phone_edit.setFixedHeight(35)
        password_label.setScaledContents(True)
        password_label.setFixedSize(36, 35)
        self.password_edit.setFixedHeight(35)
        self.setLayout(layout)
        self.setMaximumWidth(500)
        # 样式
        self.setStyleSheet(
            "#phoneError,#psdError,#loginError{color:rgb(200,50,30)}"
            "#loginBtn{background-color:rgb(46,158,224);color: rgb(240,240,240);font-weight:bold;min-height:28px;border:none;}"
            "#loginBtn:pressed{background-color:rgb(28,76,202);}"
        )


class RegisterUI(QWidget):
    """ 注册页面 含编辑框鼠标事件的处理"""

    check_phone_unique = pyqtSignal(str)  # 手机号是否唯一的请求信号

    def __init__(self, *args, **kwargs):
        super(RegisterUI, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel(self)
        username_label.setPixmap(QPixmap('media/passport_icon/username.png'))
        username_label.setFixedSize(36, 35)
        username_label.setScaledContents(True)
        username_layout.addWidget(username_label)
        self.username_edit = QLineEdit(self)
        self.username_edit.setFixedHeight(35)
        self.username_edit.setPlaceholderText("用户名/昵称")
        # self.username_edit.editingFinished.connect(self.username_edit_finished)
        self.username_edit.textEdited.connect(self.editing_username)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        # 用户名错误提示框
        self.username_error = QLabel(self)
        self.username_error.setObjectName("phoneError")
        layout.addWidget(self.username_error)

        # 手机
        phone_layout = QHBoxLayout()
        phone_label = QLabel(self)
        phone_label.setPixmap(QPixmap('media/passport_icon/phone.png'))
        phone_layout.addWidget(phone_label)
        self.phone_edit = QLineEdit(self)
        self.phone_edit.setPlaceholderText("手机号")
        self.phone_edit.editingFinished.connect(self.phone_edit_finished)
        self.phone_edit.textEdited.connect(self.editing_phone)
        phone_layout.addWidget(self.phone_edit)
        layout.addLayout(phone_layout)
        # 手机号错误提示框
        self.phone_error = QLabel(self)
        self.phone_error.setObjectName("phoneError")
        layout.addWidget(self.phone_error)

        # 邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel(self)
        email_label.setPixmap(QPixmap('media/passport_icon/email.png'))
        email_layout.addWidget(email_label)
        self.email_edit = QLineEdit(self)
        self.email_edit.setFixedHeight(35)
        self.email_edit.setPlaceholderText("邮箱(用于找回密码)")
        email_layout.addWidget(self.email_edit)
        layout.addLayout(email_layout)
        # 手机号错误提示框
        self.email_error = QLabel(self)
        self.email_error.setObjectName("emailError")
        layout.addWidget(self.email_error)

        # 密码0
        psd_layout = QHBoxLayout()
        password_label = QLabel(self)
        password_label.setPixmap(QPixmap('media/passport_icon/password.png'))
        psd_layout.addWidget(password_label)
        self.password_edit_0 = QLineEdit(self)
        self.password_edit_0.setEchoMode(QLineEdit.Password)
        self.password_edit_0.setFixedHeight(35)
        self.password_edit_0.setPlaceholderText("设置密码")
        psd_layout.addWidget(self.password_edit_0)
        layout.addLayout(psd_layout)
        # 密码错误提示框
        self.password_error_0 = QLabel(self)
        self.password_error_0.setObjectName("psdError")
        layout.addWidget(self.password_error_0)

        # 密码1
        psd_layout = QHBoxLayout()
        password_label = QLabel(self)
        password_label.setPixmap(QPixmap('media/passport_icon/password.png'))
        psd_layout.addWidget(password_label)
        self.password_edit_1 = QLineEdit(self)
        self.password_edit_1.setEchoMode(QLineEdit.Password)
        self.password_edit_1.setFixedHeight(35)
        self.password_edit_1.setPlaceholderText("再次确认密码")
        psd_layout.addWidget(self.password_edit_1)
        layout.addLayout(psd_layout)
        # 密码错误提示框
        self.password_error_1 = QLabel(self)
        self.password_error_1.setObjectName("psdError")
        layout.addWidget(self.password_error_1)

        # 验证码
        verify_layout = QHBoxLayout()
        image_code_label = QLabel(self)
        image_code_label.setPixmap(QPixmap('media/passport_icon/yanzheng.png'))
        image_code_label.setScaledContents(True)
        verify_layout.addWidget(image_code_label)
        self.image_code_edit = QLineEdit(self)
        self.image_code_edit.setPlaceholderText('填写右侧验证码')
        self.image_code_edit.setFixedHeight(35)
        verify_layout.addWidget(self.image_code_edit)
        self.image_code_show = ImageCodeLabel("获取验证码···", self)
        self.image_code_show.setMaximumSize(80, 36)
        verify_layout.addWidget(self.image_code_show)
        layout.addLayout(verify_layout)

        # 注册错误框
        self.register_error = QLabel(self)
        self.register_error.setObjectName("loginError")
        layout.addWidget(self.register_error)
        # 确认注册
        confirm_layout = QHBoxLayout()
        self.to_login_button = QPushButton("已有账户,现在登录->", self)
        confirm_layout.addWidget(self.to_login_button)
        confirm_layout.addStretch()
        self.register_button = QPushButton('立即注册 ', self)
        self.register_button.setObjectName("loginBtn")
        self.register_button.setMinimumWidth(200)
        confirm_layout.addWidget(self.register_button)
        layout.addLayout(confirm_layout)

        phone_label.setFixedSize(36, 35)
        phone_label.setScaledContents(True)
        self.phone_edit.setFixedHeight(35)
        password_label.setScaledContents(True)
        password_label.setFixedSize(36, 35)
        self.setLayout(layout)
        self.setMaximumWidth(500)
        # 样式
        self.setStyleSheet(
            "#phoneError,#psdError,#loginError,#emailError{color:rgb(200,50,30)}"
            "#loginBtn{background-color:rgb(46,158,224);color: rgb(240,240,240);font-weight:bold;min-height:28px;border:none;}"
            "#loginBtn:pressed{background-color:rgb(28,76,202);}"
        )

    def username_edit_finished(self):
        """ 编辑用户名结束 """
        pass

    def editing_username(self):
        """ 编辑用户名 """
        self.username_error.setText("")

    def phone_edit_finished(self):
        """ 编辑手机号结束 """
        self.check_phone_unique.emit(self.phone_edit.text().strip())

    def editing_phone(self):
        """ 编辑手机号 """
        self.phone_error.setText("")


class PassportUI(QStackedWidget):
    def __init__(self, *args, **kwargs):
        super(PassportUI, self).__init__(*args, **kwargs)
        # 登录界面
        self.login_widget = LoginUI(self)
        login_ = QWidget(self)
        login_layout = QVBoxLayout()
        login_layout.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(self.login_widget)
        login_.setLayout(login_layout)

        # 注册界面
        self.register_widget = RegisterUI(self)
        register_ = QWidget(self)
        register_layout = QVBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)
        register_layout.addWidget(self.register_widget)
        register_.setLayout(register_layout)

        self.addWidget(login_)
        self.addWidget(register_)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("media/passport_icon/passport_bg.png"), QRect())
