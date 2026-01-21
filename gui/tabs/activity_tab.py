from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QLineEdit, QCheckBox,
                             QSpinBox, QGroupBox, QComboBox, QMessageBox, QScrollArea)
from gui.custom_widgets import AnimatedComboBox
from gui.threads import ActivityWorker
import json
import os
from core.utils import get_user_data_path


class ActivityTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_messages()
        self.refresh_profiles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scroll_content")  # ФИКС РАМОК
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Профиль
        top_group = QGroupBox("Запуск")
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Профиль:"))
        self.profile_combo = AnimatedComboBox()
        self.profile_combo.setMinimumHeight(40)
        top_layout.addWidget(self.profile_combo, 1)

        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(40, 40)
        btn_refresh.clicked.connect(self.refresh_profiles)
        top_layout.addWidget(btn_refresh)

        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        # 2. Режимы
        mode_group = QGroupBox("Режим работы")
        mode_layout = QVBoxLayout()
        self.check_chat = QCheckBox("1. Рассылка в чатах (по работодателям)")
        self.check_resume = QCheckBox("2. Поднятие резюме в поиске")
        mode_layout.addWidget(self.check_chat)
        mode_layout.addWidget(self.check_resume)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 3. Настройки чатов
        chat_group = QGroupBox("Настройки чата")
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(15)

        limits_layout = QHBoxLayout()
        self.spin_employers = QSpinBox()
        self.spin_employers.setRange(1, 50);
        self.spin_employers.setValue(5)
        self.spin_employers.setMinimumHeight(35)
        self.spin_employers.setMinimumWidth(80)

        self.spin_msgs_per_hr = QSpinBox()
        self.spin_msgs_per_hr.setRange(1, 10);
        self.spin_msgs_per_hr.setValue(2)
        self.spin_msgs_per_hr.setMinimumHeight(35)
        self.spin_msgs_per_hr.setMinimumWidth(80)

        limits_layout.addWidget(QLabel("Работодателей:"))
        limits_layout.addWidget(self.spin_employers)
        limits_layout.addSpacing(20)
        limits_layout.addWidget(QLabel("Сообщений HR:"))
        limits_layout.addWidget(self.spin_msgs_per_hr)
        limits_layout.addStretch()
        chat_layout.addLayout(limits_layout)

        chat_layout.addWidget(QLabel("Список сообщений:"))
        self.msg_list = QListWidget()
        self.msg_list.setMinimumHeight(200)
        self.msg_list.setMaximumHeight(400)
        chat_layout.addWidget(self.msg_list)

        add_layout = QHBoxLayout()
        self.new_msg_input = QLineEdit()
        self.new_msg_input.setPlaceholderText("Текст сообщения...")
        self.new_msg_input.setMinimumHeight(40)

        btn_add = QPushButton("Добавить")
        btn_add.setMinimumHeight(40)
        btn_add.clicked.connect(self.add_message)

        btn_del = QPushButton("Удалить")
        btn_del.setMinimumHeight(40)
        btn_del.clicked.connect(self.del_message)

        add_layout.addWidget(self.new_msg_input, 1)
        add_layout.addWidget(btn_add)
        add_layout.addWidget(btn_del)
        chat_layout.addLayout(add_layout)

        chat_group.setLayout(chat_layout)
        layout.addWidget(chat_group)

        self.start_btn = QPushButton("ЗАПУСТИТЬ АКТИВНОСТЬ")
        self.start_btn.setMinimumHeight(60)
        layout.addWidget(self.start_btn)

        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    # Методы без изменений...
    def collect_data(self):
        return {
            "use_chat": self.check_chat.isChecked(),
            "use_resume": self.check_resume.isChecked(),
            "max_employers": self.spin_employers.value(),
            "msgs_per_hr": self.spin_msgs_per_hr.value(),
            "messages": [self.msg_list.item(i).text() for i in range(self.msg_list.count())],
            "profile": self.profile_combo.currentText()
        }

    def refresh_profiles(self):
        curr = self.profile_combo.currentText()
        self.profile_combo.clear()
        # Получаем путь через утилиту
        profiles_dir = get_user_data_path("profiles")

        # Создаем список перед использованием
        files = []
        if os.path.exists(profiles_dir):
            files = [f.replace(".json", "") for f in os.listdir(profiles_dir) if f.endswith(".json")]

        self.profile_combo.addItems(files)
        if curr in files: self.profile_combo.setCurrentText(curr)

    def add_message(self):
        if self.new_msg_input.text():
            self.msg_list.addItem(self.new_msg_input.text());
            self.new_msg_input.clear();
            self.save_messages()

    def del_message(self):
        if self.msg_list.currentRow() >= 0: self.msg_list.takeItem(self.msg_list.currentRow()); self.save_messages()

    def save_messages(self):
        try:
            with open(os.path.join("data", "messages_preset.json"), "w", encoding="utf-8") as f:
                json.dump([self.msg_list.item(i).text() for i in range(self.msg_list.count())], f, ensure_ascii=False)
        except:
            pass

    def load_messages(self):
        path = os.path.join("data", "messages_preset.json")  # Переменная пути
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.msg_list.addItems(json.load(f))
            except:
                pass