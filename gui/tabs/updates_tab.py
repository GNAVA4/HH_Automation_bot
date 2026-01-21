from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QTextBrowser, QGroupBox, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from gui.threads import UpdateWorker
from core.config import CURRENT_VERSION


class UpdatesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 1. Заголовок и текущая версия
        header_layout = QVBoxLayout()
        title = QLabel("Проверка обновлений")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #cba6f7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.version_label = QLabel(f"Текущая версия: {CURRENT_VERSION}")
        self.version_label.setStyleSheet("font-size: 16px; color: #a6adc8;")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(self.version_label)
        layout.addLayout(header_layout)

        # 2. Статус и Кнопка проверки
        status_box = QGroupBox()
        status_box.setStyleSheet("QGroupBox { border: none; background: rgba(30, 30, 46, 0.5); border-radius: 15px; }")
        status_layout = QVBoxLayout()

        self.status_text = QLabel("Нажмите кнопку для проверки")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_text.setStyleSheet("font-size: 16px; color: #cdd6f4;")

        self.check_btn = QPushButton("Проверить обновления")
        self.check_btn.setMinimumHeight(50)
        self.check_btn.setFixedWidth(250)
        # Стиль кнопки (Синий)
        self.check_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #89b4fa, stop:1 #cba6f7);
                color: #1e1e2e; border-radius: 12px; font-weight: bold; font-size: 15px;
            }
            QPushButton:hover { background: #b4befe; }
        """)
        self.check_btn.clicked.connect(self.check_for_updates)

        # Кнопка скачивания (Скрыта по умолчанию)
        self.download_btn = QPushButton("Скачать новую версию")
        self.download_btn.setMinimumHeight(50)
        self.download_btn.setFixedWidth(250)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a6e3a1, stop:1 #94e2d5);
                color: #1e1e2e; border-radius: 12px; font-weight: bold; font-size: 15px;
            }
            QPushButton:hover { background: #c6eef8; }
        """)
        self.download_btn.clicked.connect(self.open_download_link)
        self.download_btn.hide()

        status_layout.addWidget(self.status_text)
        status_layout.addWidget(self.check_btn, 0, Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.download_btn, 0, Qt.AlignmentFlag.AlignCenter)
        status_box.setLayout(status_layout)
        layout.addWidget(status_box)

        # 3. Список изменений (Changelog)
        self.changelog_area = QTextBrowser()
        self.changelog_area.setPlaceholderText("Здесь будет информация об обновлении...")
        self.changelog_area.setStyleSheet("""
            QTextBrowser {
                background-color: #11111b; border: 1px solid #45475a; 
                border-radius: 10px; color: #cdd6f4; padding: 10px;
            }
        """)
        self.changelog_area.hide()  # Скрыт, пока нет инфо
        layout.addWidget(self.changelog_area)

        # 4. Инструкция по обновлению (Важно!)
        self.info_box = QGroupBox()
        self.info_box.setStyleSheet(
            "QGroupBox { border: 1px solid #fab387; border-radius: 10px; background: rgba(250, 179, 135, 0.05); }")
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "<b>⚠️ ВАЖНО ПРИ ОБНОВЛЕНИИ:</b><br><br>"
            "Так как это портативная версия, ваши данные (профили, настройки) хранятся в папке <b>user_data</b>.<br>"
            "При скачивании новой версии:<br>"
            "1. Распакуйте новый архив.<br>"
            "2. Перенесите папку <b>user_data</b> из старой версии в новую.<br>"
            "3. Ваши аккаунты и настройки сохранятся."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #fab387; font-size: 13px;")

        info_layout.addWidget(info_text)
        self.info_box.setLayout(info_layout)
        self.info_box.hide()  # Показываем только если есть обнова
        layout.addWidget(self.info_box)

        layout.addStretch()

    def check_for_updates(self):
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Проверка...")
        self.status_text.setText("Связываюсь с сервером...")

        self.worker = UpdateWorker()
        self.worker.finished_signal.connect(self.on_check_finished)
        self.worker.start()

    def on_check_finished(self, data):
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Проверить снова")

        if not data:
            self.status_text.setText("❌ Ошибка соединения. Проверьте интернет.")
            return

        remote_version = data.get("version", "0.0")
        self.download_url = data.get("download_url", "")
        notes = data.get("release_notes", "")

        # Сравнение версий (простое строковое или float)
        # Лучше сравнивать как строки, если формат "3.0"
        if remote_version != CURRENT_VERSION.split()[0]:  # Сравниваем только номер "3.0"
            self.status_text.setText(f"🎉 Доступна новая версия: {remote_version}")
            self.status_text.setStyleSheet("font-size: 18px; color: #a6e3a1; font-weight: bold;")

            self.changelog_area.setHtml(notes)
            self.changelog_area.show()
            self.download_btn.show()
            self.info_box.show()
        else:
            self.status_text.setText("✅ У вас установлена последняя версия")
            self.status_text.setStyleSheet("font-size: 16px; color: #cdd6f4;")
            self.changelog_area.hide()
            self.download_btn.hide()
            self.info_box.hide()

    def open_download_link(self):
        if hasattr(self, 'download_url') and self.download_url:
            QDesktopServices.openUrl(QUrl(self.download_url))