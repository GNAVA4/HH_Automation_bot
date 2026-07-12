from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
                             QMessageBox, QLabel, QPushButton)
from PyQt6.QtCore import pyqtSlot, QSize, Qt, QTimer
from PyQt6.QtGui import QGuiApplication, QIcon, QPixmap, QPainter, QColor
import logging
import os

from core.utils import get_resource_path
from core.config import CURRENT_VERSION
from database.db_manager import DBManager

from gui.tabs.response_tab import ResponseTab
from gui.tabs.activity_tab import ActivityTab
from gui.tabs.stats_tab import StatsTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.diagnostics_tab import DiagnosticsTab
from gui.tabs.about_tab import AboutTab
from gui.tabs.tests_tab import TestsTab

from core.logger import setup_logger
from gui.threads import SearchWorker, ActivityWorker
from gui.tabs.updates_tab import UpdatesTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"HH Automation Bot v{CURRENT_VERSION}")

        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.55)
        height = int(screen.height() * 0.9)
        self.resize(width, height)
        self.move(int((screen.width() - width) / 2), int((screen.height() - height) / 2))
        self.setWindowOpacity(0.95)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setFrameShape(QListWidget.Shape.NoFrame)
        self.sidebar.currentRowChanged.connect(self.change_page)

        self.sidebar.setIconSize(QSize(20, 20))
        menu_items = ["Отклики", "Активность", "Тесты", "Статистика", "Настройки", "Диагностика", "Обновления", "О приложении"]
        self.menu_icon_files = ["menu_otkliki.svg", "menu_activity.svg", "menu_tests.svg",
                                "menu_stats.svg", "menu_settings.svg", "menu_diagnostics.svg",
                                "menu_updates.svg", "menu_about.svg"]
        for text in menu_items:
            self.sidebar.addItem(QListWidgetItem(text))
        self._update_menu_icons(0)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        # === СТАТУС-ХЕДЕР ===
        self.header = QWidget()
        self.header.setObjectName("header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(18, 12, 18, 12)
        self.header_profile = QLabel("Профиль: —")
        self.header_profile.setStyleSheet("font-weight: 700; color: #cdd6f4;")
        self.header_stats = QLabel("Откликов сегодня: 0 / 0")
        self.header_stats.setStyleSheet("color: #a6adc8;")
        self.header_status = QLabel("● Ожидание")
        self.header_status.setStyleSheet("color: #6c7086; font-weight: 700;")
        header_layout.addWidget(self.header_profile)
        header_layout.addStretch()
        header_layout.addWidget(self.header_stats)
        header_layout.addSpacing(18)
        header_layout.addWidget(self.header_status)
        right_layout.addWidget(self.header)

        self.db = DBManager()

        self.pages = QStackedWidget()
        self.response_tab = ResponseTab()
        self.activity_tab = ActivityTab()
        self.tests_tab = TestsTab()
        self.stats_tab = StatsTab()
        self.settings_tab = SettingsTab()
        self.diagnostics_tab = DiagnosticsTab()
        self.updates_tab = UpdatesTab()
        self.about_tab = AboutTab()

        self.pages.addWidget(self.response_tab)
        self.pages.addWidget(self.activity_tab)
        self.pages.addWidget(self.tests_tab)
        self.pages.addWidget(self.stats_tab)
        self.pages.addWidget(self.settings_tab)
        self.pages.addWidget(self.diagnostics_tab)
        self.pages.addWidget(self.updates_tab)
        self.pages.addWidget(self.about_tab)

        right_layout.addWidget(self.pages)

        # Заголовок лога + очистка
        log_header = QHBoxLayout()
        log_title = QLabel("Лог")
        log_title.setStyleSheet("color: #89b4fa; font-weight: 800; font-size: 13px;")
        btn_clear_log = QPushButton("Очистить")
        btn_clear_log.setObjectName("ghost")
        btn_clear_log.setFixedHeight(28)
        btn_clear_log.clicked.connect(lambda: self.log_area.clear())
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(btn_clear_log)
        right_layout.addLayout(log_header)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(90);
        self.log_area.setMaximumHeight(200)
        right_layout.addWidget(self.log_area)

        main_h_layout.addWidget(self.sidebar)
        main_h_layout.addWidget(right_widget)

        self.logger, self.gui_log_handler = setup_logger()
        self.gui_log_handler.log_signal.connect(self.append_log)
        self.search_workers = {}
        self.activity_workers = {}

        self.response_tab.start_btn.clicked.connect(self.on_response_start)
        self.response_tab.profile_combo.currentTextChanged.connect(self.update_response_btn)
        self.response_tab.profile_combo.currentTextChanged.connect(self.update_header)
        self.activity_tab.start_btn.clicked.connect(self.on_activity_start)
        self.activity_tab.profile_combo.currentTextChanged.connect(self.update_activity_btn)
        self.activity_tab.profile_combo.currentTextChanged.connect(self.update_header)

        # Периодическое обновление статус-хедера
        self.header_timer = QTimer(self)
        self.header_timer.timeout.connect(self.update_header)
        self.header_timer.start(2500)

        self.load_styles()
        self.sidebar.setCurrentRow(0)
        self.update_header()
        self.logger.info("Интерфейс инициализирован.")

    def _tint_icon(self, filename, hex_color, size=20):
        """Загружает SVG и перекрашивает его в hex_color (по альфе)."""
        path = get_resource_path(os.path.join("resources", "icons", filename))
        src = QIcon(path).pixmap(QSize(size, size))
        if src.isNull():
            return QIcon()
        result = QPixmap(src.size())
        result.fill(Qt.GlobalColor.transparent)
        p = QPainter(result)
        p.drawPixmap(0, 0, src)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(result.rect(), QColor(hex_color))
        p.end()
        return QIcon(result)

    def _update_menu_icons(self, selected):
        """Активный пункт — тёмная иконка (на светлом градиенте), остальные — серые."""
        for i, fn in enumerate(self.menu_icon_files):
            color = "#11111b" if i == selected else "#a6adc8"
            item = self.sidebar.item(i)
            if item:
                item.setIcon(self._tint_icon(fn, color))

    def update_header(self):
        """Обновляет статус-хедер: профиль активной вкладки, отклики сегодня, статус."""
        idx = self.pages.currentIndex()
        if idx == 1:
            profile = self.activity_tab.profile_combo.currentText()
        else:
            profile = self.response_tab.profile_combo.currentText()
        self.header_profile.setText(f"Профиль: {profile or '—'}")

        try:
            _total, today = self.db.get_stats(profile or None)
        except Exception:
            today = 0
        try:
            limit = int(self.settings_tab.settings_mgr.get("limit_applications") or 0)
        except Exception:
            limit = 0
        self.header_stats.setText(f"Откликов сегодня: {today} / {limit}")

        running = bool(self.search_workers) or bool(self.activity_workers)
        if running:
            self.header_status.setText("● Работает")
            self.header_status.setStyleSheet("color: #a6e3a1; font-weight: 800;")
        else:
            self.header_status.setText("● Ожидание")
            self.header_status.setStyleSheet("color: #6c7086; font-weight: 700;")

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        self._update_menu_icons(index)
        self.update_header()
        if index == 0:
            self.response_tab.refresh_profiles()
        elif index == 1:
            self.activity_tab.refresh_profiles()
        elif index == 4:
            self.settings_tab.refresh_profiles()

    def load_styles(self):
        if os.path.exists("gui/styles.qss"):
            with open("gui/styles.qss", "r", encoding="utf-8") as f: self.setStyleSheet(f.read())

    def can_start_new_process(self, new_profile):
        total = len(self.search_workers) + len(self.activity_workers)
        if total == 0: return True
        if not self.settings_tab.settings_mgr.get("enable_multi_account"):
            QMessageBox.warning(self, "Ограничение", "Мультипоточность выключена.")
            return False
        return True

    # === ОТКЛИКИ ===
    def on_response_start(self):
        data = self.response_tab.collect_data()
        profile = data.get("profile")
        if not profile: return QMessageBox.warning(self, "Ошибка", "Выберите профиль!")
        if profile in self.search_workers:
            self.search_workers[profile].stop()
            self.response_tab.start_btn.setEnabled(False)
            return
        if not data["text"]: return QMessageBox.warning(self, "Ошибка", "Введите запрос!")
        if profile in self.activity_workers: return QMessageBox.warning(self, "Занято", "Профиль занят.")
        if not self.can_start_new_process(profile): return

        self.logger.info(f"Запуск откликов: {profile}")
        worker = SearchWorker(data, profile)
        worker.finished_signal.connect(self.handle_response_finished)
        self.search_workers[profile] = worker
        worker.start()
        self.update_response_btn()
        self.update_header()

    def handle_response_finished(self, status, profile):
        if profile in self.search_workers: del self.search_workers[profile]
        self.response_tab.start_btn.setEnabled(True)
        self.update_response_btn()
        self.update_header()

        # === ДОБАВЛЕНО: ОБРАБОТКА СТОП ===
        if status == "finished":
            QMessageBox.information(self, "Готово", f"[{profile}] Рассылка завершена!")
        elif status == "closed_by_user":
            QMessageBox.warning(self, "Прервано", f"[{profile}] Браузер закрыт.")
        elif status == "stopped":
            QMessageBox.information(self, "Стоп", f"[{profile}] Процесс остановлен пользователем.")
        elif status == "auth_error":
            QMessageBox.warning(self, "Сбой авторизации",
                                f"[{profile}] Сессия истекла или вход не выполнен.\n"
                                "Пожалуйста, удалите профиль в Настройках и добавьте его заново.")
        elif "error" in status:
            QMessageBox.critical(self, "Ошибка", f"[{profile}] {status}")

    def update_response_btn(self):
        curr = self.response_tab.profile_combo.currentText()
        if curr in self.search_workers:
            self.response_tab.start_btn.setText(f"СТОП ({curr})")
            self.response_tab.start_btn.setStyleSheet("background: #f38ba8; color: #111;")
        else:
            self.response_tab.start_btn.setText("ЗАПУСТИТЬ РАССЫЛКУ")
            self.response_tab.start_btn.setStyleSheet("")

    # === АКТИВНОСТЬ ===
    def on_activity_start(self):
        data = self.activity_tab.collect_data()
        profile = data.get("profile")
        if not profile: return QMessageBox.warning(self, "Ошибка", "Выберите профиль!")
        if profile in self.activity_workers:
            self.activity_workers[profile].stop()
            self.activity_tab.start_btn.setEnabled(False)
            return
        if not data["use_chat"] and not data["use_resume"]: return QMessageBox.warning(self, "Ошибка",
                                                                                       "Выберите режим!")
        if profile in self.search_workers: return QMessageBox.warning(self, "Занято", "Профиль занят.")
        if not self.can_start_new_process(profile): return

        self.logger.info(f"Запуск активности: {profile}")
        worker = ActivityWorker(data, profile)
        worker.finished_signal.connect(self.handle_activity_finished)
        self.activity_workers[profile] = worker
        worker.start()
        self.update_activity_btn()
        self.update_header()

    def handle_activity_finished(self, status, profile):
        if profile in self.activity_workers: del self.activity_workers[profile]
        self.activity_tab.start_btn.setEnabled(True)
        self.update_activity_btn()
        self.update_header()

        # === ДОБАВЛЕНО: ОБРАБОТКА СТОП ===
        if status == "finished":
            QMessageBox.information(self, "Готово", f"[{profile}] Активность завершена!")
        elif status == "closed_by_user":
            QMessageBox.warning(self, "Прервано", f"[{profile}] Браузер закрыт.")
        elif status == "stopped":
            QMessageBox.information(self, "Стоп", f"[{profile}] Процесс остановлен пользователем.")
        elif "error" in status:
            QMessageBox.critical(self, "Ошибка", f"[{profile}] {status}")

    def update_activity_btn(self):
        curr = self.activity_tab.profile_combo.currentText()
        if curr in self.activity_workers:
            self.activity_tab.start_btn.setText(f"СТОП ({curr})")
            self.activity_tab.start_btn.setStyleSheet("background: #f38ba8; color: #111;")
        else:
            self.activity_tab.start_btn.setText("ЗАПУСТИТЬ АКТИВНОСТЬ")
            self.activity_tab.start_btn.setStyleSheet("")

    @pyqtSlot(str)
    def append_log(self, text):
        if self.log_area:
            self.log_area.append(text)
            self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())