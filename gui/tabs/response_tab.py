import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QGroupBox, QScrollArea,
                             QPushButton, QTextEdit, QGridLayout, QInputDialog, QMessageBox, QListView)
from PyQt6.QtCore import Qt
from gui.custom_widgets import CheckableComboBox, AnimatedComboBox
from core.utils import get_user_data_path

PRESETS_FILE = get_user_data_path("presets.json")


class ResponseTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_presets_list()
        self.refresh_profiles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 1. Верхняя панель (Центрирование элементов)
        top_group = QGroupBox("Запуск")
        top_layout = QHBoxLayout()
        # Выравнивание содержимого по центру по вертикали
        top_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.profile_combo = AnimatedComboBox()
        self.profile_combo.setMinimumWidth(200);
        self.profile_combo.setMinimumHeight(45)

        self.preset_combo = AnimatedComboBox()
        self.preset_combo.addItem("По умолчанию")
        self.preset_combo.setMinimumWidth(200);
        self.preset_combo.setMinimumHeight(45)
        self.preset_combo.currentIndexChanged.connect(self.load_selected_preset)

        btn_save = QPushButton("Сохранить")
        btn_save.setFixedSize(120, 45)
        btn_save.clicked.connect(self.save_preset)

        btn_del = QPushButton("Удалить")
        btn_del.setFixedSize(120, 45)
        btn_del.clicked.connect(self.delete_preset)

        # Добавляем виджеты с выравниванием
        top_layout.addWidget(QLabel("Профиль:"), 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.profile_combo, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Пресет:"), 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.preset_combo, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addStretch()
        top_layout.addWidget(btn_save, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(btn_del, 0, Qt.AlignmentFlag.AlignVCenter)

        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)

        # 2. Фильтры
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent")
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(25)
        grid.setColumnStretch(1, 1);
        grid.setColumnStretch(3, 1)

        def add_field(row, col, text, widget):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: 700; color: #bac2de;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            widget.setMinimumHeight(45)
            grid.addWidget(lbl, row, col)
            grid.addWidget(widget, row, col + 1)

        self.search_input = QLineEdit();
        self.search_input.setPlaceholderText("Аналитик данных")
        add_field(0, 0, "Поиск вакансии:", self.search_input)
        self.exclude_input = QLineEdit();
        self.exclude_input.setPlaceholderText("Например: Сбер, Yandex, Авито, Data Scientist и тд.")
        add_field(0, 2, "Исключить слова:", self.exclude_input)

        self.salary_input = QLineEdit();
        self.salary_input.setPlaceholderText("Не рекомендуется указывать")
        add_field(1, 0, "Доход от (руб):", self.salary_input)
        self.region_combo = AnimatedComboBox()  # Анимированный
        self.region_combo.addItems(
            ["Все регионы", "Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань"])
        add_field(1, 2, "Регион:", self.region_combo)

        # Множественные (Checkable)
        self.exp_combo = CheckableComboBox()
        self.exp_combo.addItems({"Нет опыта": "noExperience", "1-3 года": "between1And3", "3-6 лет": "between3And6",
                                 "Более 6 лет": "moreThan6"})
        add_field(2, 0, "Опыт работы:", self.exp_combo)
        self.employment_combo = CheckableComboBox()
        self.employment_combo.addItems({"Полная": "FULL", "Частичная": "PART", "ГПХ": "GPH", "Стажировка": "PROBATION"})
        add_field(2, 2, "Тип занятости:", self.employment_combo)

        self.work_format_combo = CheckableComboBox()
        self.work_format_combo.addItems({"В офисе": "ON_SITE", "Удаленно": "REMOTE", "Гибрид": "HYBRID"})
        add_field(3, 0, "Формат работы:", self.work_format_combo)
        self.schedule_combo = CheckableComboBox()
        self.schedule_combo.addItems({"Полный день": "fullDay", "Сменный": "shift", "Гибкий": "flexible"})
        add_field(3, 2, "График (доп):", self.schedule_combo)

        self.edu_combo = CheckableComboBox()
        self.edu_combo.addItems({"Не важно": "not_required_or_not_specified", "Высшее": "higher"})
        add_field(4, 0, "Образование:", self.edu_combo)
        self.other_combo = CheckableComboBox()
        self.other_combo.addItems(
            {"Аккредитованные IT": "accredited_it", "С 14 лет": "accept_kids", "< 10 откликов": "low_performance"})
        add_field(4, 2, "Другие параметры:", self.other_combo)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # 3. Резюме (Компактнее сверху)
        resp_group = QGroupBox("Резюме и сопроводительное письмо")
        resp_layout = QGridLayout()
        # Уменьшил верхний отступ до 15 (было 25)
        resp_layout.setContentsMargins(15, 15, 15, 15)

        self.resume_input = QLineEdit()
        self.resume_input.setPlaceholderText("Название резюме (Обязательно)")
        self.resume_input.setMinimumHeight(45)
        resp_layout.addWidget(QLabel("Резюме:"), 0, 0)
        resp_layout.addWidget(self.resume_input, 0, 1)

        self.letter_edit = QTextEdit()
        self.letter_edit.setPlaceholderText("Здравствуйте! {vacancy}...")
        self.letter_edit.setMaximumHeight(60)
        resp_layout.addWidget(QLabel("Текст:"), 1, 0)
        resp_layout.addWidget(self.letter_edit, 1, 1)

        resp_group.setLayout(resp_layout)
        main_layout.addWidget(resp_group)

        # 4. Кнопка
        self.start_btn = QPushButton("ЗАПУСТИТЬ РАССЫЛКУ")
        self.start_btn.setMinimumHeight(60)
        main_layout.addWidget(self.start_btn)

    def refresh_profiles(self):
        current = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()

        # Используем AppData
        profiles_dir = get_user_data_path("profiles")
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)

        # Инициализируем список ЗАРАНЕЕ
        files = []
        if os.path.exists(profiles_dir):
            files = [f.replace(".json", "") for f in os.listdir(profiles_dir) if f.endswith(".json")]

        self.profile_combo.addItems(files)
        if current in files:
            self.profile_combo.setCurrentText(current)
        self.profile_combo.blockSignals(False)

    def collect_data(self):
        return {
            "text": self.search_input.text(),
            "excluded_text": self.exclude_input.text(),
            "salary": self.salary_input.text(),
            "area": self.region_combo.currentText(),
            "experience": self.exp_combo.get_checked_data(),
            "employment_form": self.employment_combo.get_checked_data(),
            "work_format": self.work_format_combo.get_checked_data(),
            "schedule": self.schedule_combo.get_checked_data(),
            "education": self.edu_combo.get_checked_data(),
            "label": self.other_combo.get_checked_data(),
            "resume_name": self.resume_input.text(),
            "cover_letter": self.letter_edit.toPlainText(),
            "profile": self.profile_combo.currentText()
        }

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Сохранение", "Название пресета:")
        if ok and name:
            data = self.collect_data()
            presets = self.get_all_presets()
            presets[name] = data
            with open(PRESETS_FILE, "w", encoding="utf-8") as f: json.dump(presets, f, indent=4)
            self.load_presets_list()
            self.preset_combo.setCurrentText(name)

    def load_presets_list(self):
        self.preset_combo.blockSignals(True); self.preset_combo.clear(); self.preset_combo.addItem("Выберите пресет...")
        presets = self.get_all_presets()
        self.preset_combo.addItems(presets.keys()); self.preset_combo.blockSignals(False)

    def get_all_presets(self):
        if not os.path.exists(PRESETS_FILE): return {}
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def load_selected_preset(self):
        name = self.preset_combo.currentText()
        presets = self.get_all_presets()
        if name in presets:
            data = presets[name]
            self.search_input.setText(data.get("text", ""))
            self.exclude_input.setText(data.get("excluded_text", ""))
            self.salary_input.setText(data.get("salary", ""))
            self.region_combo.setCurrentText(data.get("area", "Все регионы"))
            self.resume_input.setText(data.get("resume_name", ""))
            self.letter_edit.setPlainText(data.get("cover_letter", ""))
            self.exp_combo.set_checked_by_data(data.get("experience", []))
            self.employment_combo.set_checked_by_data(data.get("employment_form", []))
            self.work_format_combo.set_checked_by_data(data.get("work_format", []))
            self.schedule_combo.set_checked_by_data(data.get("schedule", []))
            self.edu_combo.set_checked_by_data(data.get("education", []))
            self.other_combo.set_checked_by_data(data.get("label", []))

    def delete_preset(self):
        name = self.preset_combo.currentText()
        presets = self.get_all_presets()
        if name in presets:
            del presets[name]
            with open(PRESETS_FILE, "w", encoding="utf-8") as f: json.dump(presets, f)
            self.load_presets_list()