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

        # Таймер автообновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(3000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # === Верхняя панель ===
        top_layout = QHBoxLayout()

        self.total_label = QLabel("Всего: 0")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")

        self.today_label = QLabel("Сегодня: 0")
        self.today_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")

        # Профиль (Анимированный список)
        self.profile_filter = AnimatedComboBox()
        self.profile_filter.setMinimumHeight(45)
        self.profile_filter.setMinimumWidth(200)
        self.profile_filter.addItem("Все профили")
        self.profile_filter.currentTextChanged.connect(self.refresh_stats)

        # Кнопка Обновить
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

        # === Таблица ===
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Вакансия", "Компания", "Профиль", "Время"])
        self.table.setAlternatingRowColors(True)

        # Стилизация таблицы
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
                color: #cba6f7; /* Цвет заголовков */
                font-weight: bold;
                padding: 5px;
                border: 1px solid #1e1e2e;
            }
        """)

        # === НАСТРОЙКА ШИРИНЫ СТОЛБЦОВ ===
        header = self.table.horizontalHeader()

        # 1. Разрешаем пользователю менять ширину мышкой
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 2. Растягиваем последнюю колонку (Время) до конца окна
        header.setStretchLastSection(True)

        # 3. Задаем начальные размеры (пиксели)
        self.table.setColumnWidth(0, 300)  # Вакансия (уменьшена)
        self.table.setColumnWidth(1, 400)  # Компания (увеличена)
        self.table.setColumnWidth(2, 150)  # Профиль (компактно)
        # 4-я колонка (Время) займет всё оставшееся место

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
        for i, (title, company, timestamp, profile) in enumerate(rows):
            if profile: all_profiles.add(profile)

            # Создаем ячейки (только для чтения)
            item_title = QTableWidgetItem(str(title))
            item_title.setFlags(item_title.flags() ^ Qt.ItemFlag.ItemIsEditable)

            item_company = QTableWidgetItem(str(company))
            item_company.setFlags(item_company.flags() ^ Qt.ItemFlag.ItemIsEditable)

            item_profile = QTableWidgetItem(str(profile))
            item_profile.setFlags(item_profile.flags() ^ Qt.ItemFlag.ItemIsEditable)

            item_time = QTableWidgetItem(str(timestamp).split('.')[0])
            item_time.setFlags(item_time.flags() ^ Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(i, 0, item_title)
            self.table.setItem(i, 1, item_company)
            self.table.setItem(i, 2, item_profile)
            self.table.setItem(i, 3, item_time)

        # Обновляем фильтр
        current_items = [self.profile_filter.itemText(i) for i in range(self.profile_filter.count())]
        for p in all_profiles:
            if p not in current_items:
                self.profile_filter.addItem(p)