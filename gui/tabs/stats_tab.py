from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from database.db_manager import DBManager
from gui.custom_widgets import AnimatedComboBox


class StatsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(3000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Верхняя панель
        top_layout = QHBoxLayout()

        self.total_label = QLabel("Всего: 0")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")

        self.today_label = QLabel("Сегодня: 0")
        self.today_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")

        # Профиль
        self.profile_filter = AnimatedComboBox()
        self.profile_filter.setMinimumHeight(45)
        self.profile_filter.setMinimumWidth(200)
        self.profile_filter.addItem("Все профили")
        self.profile_filter.currentTextChanged.connect(self.refresh_stats)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setMinimumHeight(45)
        refresh_btn.clicked.connect(self.refresh_stats)

        top_layout.addWidget(self.total_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.today_label)
        top_layout.addStretch()

        top_layout.addWidget(QLabel("Фильтр:"))
        top_layout.addWidget(self.profile_filter)
        top_layout.addWidget(refresh_btn)

        layout.addLayout(top_layout)

        # === ТАБЛИЦА ===
        self.table = QTableWidget()
        # ИЗМЕНЕНИЕ: 5 колонок вместо 4
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Вакансия", "Компания", "Профиль", "Резюме", "Время"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cba6f7;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #1e1e2e;
            }
        """)

        # Ширина столбцов
        self.table.setColumnWidth(0, 250)  # Вакансия
        self.table.setColumnWidth(1, 200)  # Компания
        self.table.setColumnWidth(2, 120)  # Профиль
        self.table.setColumnWidth(3, 150)  # Резюме (НОВОЕ)
        # Время растянется

        layout.addWidget(self.table)
        self.refresh_stats()

    def refresh_stats(self):
        filter_val = self.profile_filter.currentText()
        db_filter = None if filter_val == "Все профили" else filter_val

        total, today = self.db.get_stats(db_filter)
        self.total_label.setText(f"Всего: {total}")
        self.today_label.setText(f"Сегодня: {today}")

        rows = self.db.get_all_applications(db_filter)
        self.table.setRowCount(len(rows))

        all_profiles = set()

        # ИЗМЕНЕНИЕ: Распаковываем 5 значений (resume_used добавился в SQL)
        # Порядок в SQL: vacancy_title, company_name, timestamp, profile, resume_used
        for i, (title, company, timestamp, profile, resume) in enumerate(rows):
            if profile: all_profiles.add(profile)

            # Хелпер для создания ячеек
            def make_item(text):
                item = QTableWidgetItem(str(text))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                return item

            self.table.setItem(i, 0, make_item(title))
            self.table.setItem(i, 1, make_item(company))
            self.table.setItem(i, 2, make_item(profile))
            self.table.setItem(i, 3, make_item(resume if resume else "-"))  # Колонка Резюме
            self.table.setItem(i, 4, make_item(str(timestamp).split('.')[0]))

        current_items = [self.profile_filter.itemText(i) for i in range(self.profile_filter.count())]
        for p in all_profiles:
            if p not in current_items:
                self.profile_filter.addItem(p)