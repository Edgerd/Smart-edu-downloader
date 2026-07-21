# -*- coding: utf-8 -*-
"""qfluentwidgets 推荐组件综合演示。

展示 InfoBar、MessageBox、SettingCardGroup/SettingCard、CardWidget 等
组件在实际项目中的用法，便于评估是否集成到主程序。
"""

import sys
import io

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

# 静默导入，避免 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    import qfluentwidgets
finally:
    sys.stdout = _old_stdout

from qfluentwidgets import (
    setTheme, Theme, setThemeColor,
    InfoBar, InfoBarPosition,
    MessageBox,
    CardWidget, ElevatedCardWidget,
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard,
    PushSettingCard, RangeSettingCard,
    PushButton,
    FluentIcon as FIF,
    OptionsConfigItem, OptionsValidator,
    RangeConfigItem, RangeValidator,
)

from gui.fonts import init_fonts, body_font, bold_font
from gui.styles import load_primary_color


class DemoWindow(QWidget):
    """qfluentwidgets 组件演示窗口"""

    def __init__(self):
        super().__init__()
        self._accent_color = load_primary_color()
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("qfluentwidgets 推荐组件演示")
        self.resize(800, 700)
        self.setFont(body_font())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self._create_info_bar_section(layout)
        self._create_message_box_section(layout)
        self._create_card_section(layout)
        self._create_setting_card_section(layout)

        layout.addStretch()

    def _create_info_bar_section(self, parent_layout):
        """InfoBar 提示区域"""
        title = QLabel("1. InfoBar 非阻塞提示")
        title.setFont(bold_font())
        parent_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(10)

        for kind, text, color in [
            ("success", "成功提示", "#28A745"),
            ("warning", "警告提示", "#FFC107"),
            ("error", "错误提示", "#DC3545"),
            ("info", "普通信息", "#17A2B8"),
        ]:
            btn = PushButton(text)
            btn.setFont(body_font())
            btn.clicked.connect(lambda checked, k=kind: self._show_info_bar(k))
            row.addWidget(btn)

        row.addStretch()
        parent_layout.addLayout(row)

    def _show_info_bar(self, kind: str):
        """显示对应类型的 InfoBar"""
        if kind == "success":
            InfoBar.success(
                title="操作成功",
                content="已添加到下载列表",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            ).show()
        elif kind == "warning":
            InfoBar.warning(
                title="注意",
                content="当前网络连接不稳定",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            ).show()
        elif kind == "error":
            InfoBar.error(
                title="失败",
                content="无法解析该 URL，请检查链接",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            ).show()
        else:
            InfoBar.info(
                title="提示",
                content="请选择要下载的教材",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            ).show()

    def _create_message_box_section(self, parent_layout):
        """MessageBox 弹窗区域"""
        title = QLabel("2. Fluent MessageBox 弹窗")
        title.setFont(bold_font())
        parent_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(10)

        confirm_btn = PushButton("确认对话框")
        confirm_btn.setFont(body_font())
        confirm_btn.clicked.connect(self._show_confirm_box)
        row.addWidget(confirm_btn)

        error_btn = PushButton("错误提示")
        error_btn.setFont(body_font())
        error_btn.clicked.connect(self._show_error_box)
        row.addWidget(error_btn)

        info_btn = PushButton("信息提示")
        info_btn.setFont(body_font())
        info_btn.clicked.connect(self._show_info_box)
        row.addWidget(info_btn)

        row.addStretch()
        parent_layout.addLayout(row)

    def _show_confirm_box(self):
        """显示确认对话框"""
        box = MessageBox(
            "确认删除",
            "确定要删除这条下载记录吗？删除后无法恢复。",
            self,
        )
        box.yesButton.setText("确定")
        box.cancelButton.setText("取消")
        if box.exec():
            InfoBar.success(
                title="已删除", content="记录已移除", parent=self
            ).show()

    def _show_error_box(self):
        """显示错误提示"""
        box = MessageBox(
            "请求失败",
            "无法连接到服务器，请检查网络后重试。",
            self,
        )
        box.yesButton.setText("重试")
        box.cancelButton.setText("关闭")
        box.exec()

    def _show_info_box(self):
        """显示信息提示"""
        box = MessageBox(
            "关于",
            "Smart-edu-downloader 是一款教育平台资源下载工具。",
            self,
        )
        box.yesButton.setText("知道了")
        box.cancelButton.hide()
        box.buttonLayout.insertStretch(1)
        box.exec()

    def _create_card_section(self, parent_layout):
        """CardWidget 卡片区域"""
        title = QLabel("3. CardWidget 内容卡片")
        title.setFont(bold_font())
        parent_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)

        card1 = CardWidget()
        card1_layout = QVBoxLayout(card1)
        card1_title = QLabel("资源浏览")
        card1_title.setFont(bold_font())
        card1_desc = QLabel("浏览国家中小学智慧教育平台资源，支持多级筛选。")
        card1_desc.setFont(body_font())
        card1_desc.setWordWrap(True)
        card1_layout.addWidget(card1_title)
        card1_layout.addWidget(card1_desc)
        card1_layout.addStretch()
        card1.setFixedSize(240, 120)
        row.addWidget(card1)

        card2 = ElevatedCardWidget()
        card2_layout = QVBoxLayout(card2)
        card2_title = QLabel("下载管理")
        card2_title.setFont(bold_font())
        card2_desc = QLabel("查看下载进度、管理已下载教材和导出记录。")
        card2_desc.setFont(body_font())
        card2_desc.setWordWrap(True)
        card2_layout.addWidget(card2_title)
        card2_layout.addWidget(card2_desc)
        card2_layout.addStretch()
        card2.setFixedSize(240, 120)
        row.addWidget(card2)

        row.addStretch()
        parent_layout.addLayout(row)

    def _create_setting_card_section(self, parent_layout):
        """SettingCardGroup 设置卡片区域"""
        title = QLabel("4. SettingCardGroup 设置卡片")
        title.setFont(bold_font())
        parent_layout.addWidget(title)

        group = SettingCardGroup("界面与下载", self)

        switch_card = SwitchSettingCard(
            FIF.SETTING,
            "开机启动",
            "系统启动时自动运行本程序",
            parent=group,
        )
        switch_card.setChecked(False)
        group.addSettingCard(switch_card)

        language_config = OptionsConfigItem(
            "Demo", "Language", "zh_CN",
            OptionsValidator(["zh_CN", "en"]),
        )
        combo_card = ComboBoxSettingCard(
            language_config,
            FIF.LANGUAGE,
            "界面语言",
            "选择程序显示语言",
            texts=["简体中文", "English"],
            parent=group,
        )
        group.addSettingCard(combo_card)

        max_tasks_config = RangeConfigItem(
            "Demo", "MaxTasks", 3,
            RangeValidator(1, 10),
        )
        range_card = RangeSettingCard(
            max_tasks_config,
            FIF.VOLUME,
            "同时下载任务数",
            "调整同时进行的下载任务数量",
            parent=group,
        )
        group.addSettingCard(range_card)

        push_card = PushSettingCard(
            "选择目录",
            FIF.FOLDER,
            "下载目录",
            "设置教材和资源的默认保存位置",
            group,
        )
        group.addSettingCard(push_card)

        parent_layout.addWidget(group)


def run_demo():
    """运行 qfluentwidgets 组件演示"""
    app = QApplication(sys.argv)
    init_fonts()
    app.setFont(body_font())

    setTheme(Theme.LIGHT)
    setThemeColor(load_primary_color())

    window = DemoWindow()
    window.show()
    sys.exit(app.exec())
