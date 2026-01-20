from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QStackedWidget, QTextEdit, QMessageBox)
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QGuiApplication
import logging
import os

from gui.tabs.response_tab import ResponseTab
from gui.tabs.activity_tab import ActivityTab
from gui.tabs.stats_tab import StatsTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.diagnostics_tab import DiagnosticsTab
from gui.tabs.about_tab import AboutTab

from core.logger import setup_logger
from gui.threads import SearchWorker, ActivityWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HH Automation Bot v2.5 alpha")

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

        menu_items = ["Отклики", "Активность", "Статистика", "Настройки", "Диагностика", "О приложении"]
        for item in menu_items: self.sidebar.addItem(item)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        self.pages = QStackedWidget()
        self.response_tab = ResponseTab()
        self.activity_tab = ActivityTab()
        self.stats_tab = StatsTab()
        self.settings_tab = SettingsTab()
        self.diagnostics_tab = DiagnosticsTab()
        self.about_tab = AboutTab()

        self.pages.addWidget(self.response_tab)
        self.pages.addWidget(self.activity_tab)
        self.pages.addWidget(self.stats_tab)
        self.pages.addWidget(self.settings_tab)
        self.pages.addWidget(self.diagnostics_tab)
        self.pages.addWidget(self.about_tab)

        right_layout.addWidget(self.pages)

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
        self.activity_tab.start_btn.clicked.connect(self.on_activity_start)
        self.activity_tab.profile_combo.currentTextChanged.connect(self.update_activity_btn)

        self.load_styles()
        self.sidebar.setCurrentRow(0)
        self.logger.info("Интерфейс инициализирован.")

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        if index == 0:
            self.response_tab.refresh_profiles()
        elif index == 1:
            self.activity_tab.refresh_profiles()
        elif index == 3:
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

    def handle_response_finished(self, status, profile):
        if profile in self.search_workers: del self.search_workers[profile]
        self.response_tab.start_btn.setEnabled(True)
        self.update_response_btn()

        # === ДОБАВЛЕНО: ОБРАБОТКА СТОП ===
        if status == "finished":
            QMessageBox.information(self, "Готово", f"[{profile}] Рассылка завершена!")
        elif status == "closed_by_user":
            QMessageBox.warning(self, "Прервано", f"[{profile}] Браузер закрыт.")
        elif status == "stopped":
            QMessageBox.information(self, "Стоп", f"[{profile}] Процесс остановлен пользователем.")
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

    def handle_activity_finished(self, status, profile):
        if profile in self.activity_workers: del self.activity_workers[profile]
        self.activity_tab.start_btn.setEnabled(True)
        self.update_activity_btn()

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