# _*_ coding:utf-8 _*_
# @File  : user_data_ui.py
# @Time  : 2020-09-03 14:08
# @Author: zizle

""" 用户数据维护 (产业数据库) """

from PyQt5.QtWidgets import (QWidget, QSplitter, QHBoxLayout, QVBoxLayout, QListWidget, QTabWidget, QLabel, QComboBox, QPushButton,
                             QTableWidget, QAbstractItemView, QFrame, QLineEdit, QCheckBox, QHeaderView, QProgressBar)
from PyQt5.QtCore import QMargins, Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView


class ConfigSourceUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(ConfigSourceUI, self).__init__(*args, **kwargs)
        self.is_updating = False  # 标记是否正在执行更新
        self.current_button = None

        # 更新数据的线程
        self.updating_thread = None

        main_layout = QVBoxLayout()
        opt_layout = QHBoxLayout()
        opt_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.setMinimumWidth(80)
        opt_layout.addWidget(self.variety_combobox)

        opt_layout.addWidget(QLabel("数据组:", self))
        self.group_combobox = QComboBox(self)
        self.group_combobox.setMinimumWidth(100)
        opt_layout.addWidget(self.group_combobox)

        # 新增数据组
        self.new_group_button = QPushButton("新建组?", self)
        self.new_group_button.clicked.connect(self.to_create_new_group)
        opt_layout.addWidget(self.new_group_button)

        # 新增组的编辑框
        self.new_group_edit = QLineEdit(self)
        self.new_group_edit.setFixedWidth(120)
        self.new_group_edit.setPlaceholderText("新组名称?")
        self.new_group_edit.hide()
        opt_layout.addWidget(self.new_group_edit)

        # 新增组确定按钮
        self.confirm_group_button = QPushButton("确定", self)
        self.confirm_group_button.hide()
        opt_layout.addWidget(self.confirm_group_button)

        # 信息提示
        self.tips_message = QLabel(self)
        self.tips_message.setObjectName("messageLabel")
        opt_layout.addWidget(self.tips_message)

        # 更新数据的进度条
        self.updating_process = QProgressBar(self)
        self.updating_process.hide()
        self.updating_process.setFixedHeight(15)
        opt_layout.addWidget(self.updating_process)
        opt_layout.addStretch()

        self.new_config_button = QPushButton('调整配置', self)
        opt_layout.addWidget(self.new_config_button)
        main_layout.addLayout(opt_layout)

        self.config_table = QTableWidget(self)
        self.config_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.config_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.config_table.setFocusPolicy(Qt.NoFocus)
        self.config_table.setFrameShape(QFrame.NoFrame)
        self.config_table.setAlternatingRowColors(True)
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels(["编号", "品种", "组别", "更新路径", ""])
        self.config_table.verticalHeader().hide()
        self.config_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        main_layout.addWidget(self.config_table)

        self.config_table.setObjectName('configsTable')

        tips = "<p>1 点击右上角'更新配置'按钮，配置当前品种当前数据组更新文件所在的文件夹.</p>" \
               "<p>2 '点击更新'让系统读取文件夹内的数据表自动上传.</p>" \
               "<p>2-1 文件夹内表格格式:</p>" \
               "<p>第1行：万得导出的表第一行不动;自己创建的表第一行可留空;</p>" \
               "<p>第2行：数据表表头;</p>" \
               "<p>第3行：不做限制,可填入单位等,也可直接留空.</p>" \
               "<p>第4行：数据起始行,第一列为【日期】类型,非日期的行系统不会做读取.</p>" \
               "<p>特别注意: 文件内以`Sheet`开头的表将不做读取.即不进行命名的表系统是忽略的."

        tips_label = QLabel(tips, self)
        tips_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        tips_label.setWordWrap(True)
        tips_label.setObjectName("tipLabel")
        main_layout.addWidget(tips_label)

        self.setLayout(main_layout)
        self.setStyleSheet(
            "#tipLabel{font-size:15px;color:rgb(180,100,100)}"
            "#configsTable{background-color:rgb(240,240,240);font-size:13px;selection-color:rgb(180,60,60);"
            "alternate-background-color:rgb(245,250,248);}"
        )

    def to_create_new_group(self):
        """ 显示新增组 """
        if self.new_group_edit.isHidden():
            self.new_group_edit.show()
        else:
            self.new_group_edit.hide()
        if self.confirm_group_button.isHidden():
            self.confirm_group_button.show()
        else:
            self.confirm_group_button.hide()

    def hide_create_new_group(self):
        """ 隐藏新增组 """
        self.new_group_edit.hide()
        self.new_group_edit.clear()
        self.confirm_group_button.hide()


class VarietySheetUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(VarietySheetUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 1, 2, 1))
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.setMinimumWidth(80)
        opts_layout.addWidget(self.variety_combobox)

        opts_layout.addWidget(QLabel("数据组:", self))
        self.group_combobox = QComboBox(self)
        self.group_combobox.setMinimumWidth(100)
        opts_layout.addWidget(self.group_combobox)

        # 只看我上传选项
        self.only_me_check = QCheckBox(self)
        self.only_me_check.setText("只看我上传的")
        self.only_me_check.setChecked(True)
        # self.only_me_check.stateChanged.connect(self._get_current_tables)
        opts_layout.addWidget(self.only_me_check)

        opts_layout.addStretch()
        main_layout.addLayout(opts_layout)
        self.sheet_table = QTableWidget(self)
        self.sheet_table.setFrameShape(QFrame.NoFrame)
        self.sheet_table.verticalHeader().hide()
        self.sheet_table.setEditTriggers(QHeaderView.NoEditTriggers)
        self.sheet_table.setColumnCount(6)
        self.sheet_table.setHorizontalHeaderLabels(["编号", "创建日期", "名称", "更新日期", "增量", ""])
        self.sheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.sheet_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        main_layout.addWidget(self.sheet_table)
        self.setLayout(main_layout)


class SheetChartUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(SheetChartUI, self).__init__(*args, **kwargs)
        main_layout = QVBoxLayout()
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("品种:", self))
        self.variety_combobox = QComboBox(self)
        self.variety_combobox.setMinimumWidth(80)
        opts_layout.addWidget(self.variety_combobox)

        # 只看我上传选项
        self.only_me_check = QCheckBox(self)
        self.only_me_check.setText("只看我配置的")
        self.only_me_check.setChecked(True)
        # self.only_me_check.stateChanged.connect(self._get_current_tables)
        opts_layout.addWidget(self.only_me_check)

        opts_layout.addStretch()
        main_layout.addLayout(opts_layout)
        self.chart_table = QTableWidget(self)
        self.chart_table.hide()
        main_layout.addWidget(self.chart_table)

        # 显示所有图的网页
        self.web_container = QWebEngineView(self)
        main_layout.addWidget(self.web_container)
        self.setLayout(main_layout)


class UserDataMaintainUI(QWidget):
    def __init__(self, *args, **kwargs):
        super(UserDataMaintainUI, self).__init__(*args, **kwargs)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        main_splitter = QSplitter(self)

        self.maintain_menu = QListWidget(self)
        main_splitter.addWidget(self.maintain_menu)

        self.maintain_frame = QTabWidget(self)
        self.maintain_frame.setDocumentMode(True)
        self.maintain_frame.tabBar().hide()
        main_splitter.addWidget(self.maintain_frame)

        main_splitter.setStretchFactor(1, 2)
        main_splitter.setStretchFactor(2, 8)
        main_splitter.setHandleWidth(1)

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        self.maintain_menu.setObjectName('leftList')
        self.setStyleSheet(
            "#leftList{outline:none;border:none;border-right: 1px solid rgb(180,180,180);}"
            "#leftList::item{height:25px;}"
            "#leftList::item:selected{border-left:3px solid rgb(100,120,150);color:#000;background-color:rgb(180,220,230);}"
            "#messageLabel{color:rgb(233,66,66);font-weight:bold}"
        )

        # 实例化3个待显示的界面
        self.source_config_widget = ConfigSourceUI(self)
        self.maintain_frame.addTab(self.source_config_widget, "数据源")

        self.variety_sheet_widget = VarietySheetUI(self)
        self.maintain_frame.addTab(self.variety_sheet_widget, "数据表")

        self.sheet_chart_widget = SheetChartUI(self)
        self.maintain_frame.addTab(self.sheet_chart_widget, "数据图")


