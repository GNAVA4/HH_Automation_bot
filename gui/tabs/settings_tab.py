from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGroupBox, QScrollArea,
                             QDoubleSpinBox, QCheckBox, QFormLayout, QInputDialog, QMessageBox, QFrame)
from core.settings_manager import SettingsManager
from gui.threads import LoginWorker
from gui.custom_widgets import AnimatedComboBox
import os


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_mgr = SettingsManager()
        self.init_ui()
        self.refresh_profiles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_widget.setObjectName("scroll_content")

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Профили
        profile_group = QGroupBox("Управление аккаунтами")
        profile_layout = QHBoxLayout()
        self.profile_combo = AnimatedComboBox()
        self.profile_combo.setMinimumHeight(45)

        btn_add = QPushButton("Добавить профиль")
        btn_add.setMinimumHeight(45)
        btn_add.clicked.connect(self.add_profile)

        btn_del = QPushButton("Удалить профиль")
        btn_del.setMinimumHeight(45)
        btn_del.clicked.connect(self.delete_profile)

        profile_layout.addWidget(QLabel("Профили:"))
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(btn_add)
        profile_layout.addWidget(btn_del)
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        # 2. Лимиты
        limits_group = QGroupBox("Безопасность и Лимиты")
        form_layout = QFormLayout()

        warn_label = QLabel("⚠️ Внимание: HH.ru ограничивает отклики до 200 в сутки на один аккаунт.")
        warn_label.setStyleSheet("color: #fab387; font-style: italic;")
        warn_label.setWordWrap(True)
        form_layout.addRow(warn_label)

        self.limit_app = QDoubleSpinBox()
        self.limit_app.setDecimals(0);
        self.limit_app.setRange(1, 1000)
        self.limit_app.setValue(self.settings_mgr.get("limit_applications"))
        self.limit_app.valueChanged.connect(lambda v: self.settings_mgr.set("limit_applications", int(v)))
        form_layout.addRow("Макс. откликов за запуск:", self.limit_app)

        self.check_multi = QCheckBox("Разрешить мульти-аккаунт (одновременно)")
        self.check_multi.setChecked(self.settings_mgr.get("enable_multi_account"))
        self.check_multi.stateChanged.connect(lambda v: self.settings_mgr.set("enable_multi_account", bool(v)))
        form_layout.addRow(self.check_multi)

        limits_group.setLayout(form_layout)
        layout.addWidget(limits_group)

        # 3. Тайминги (ТУРБО РЕЖИМ)
        time_group = QGroupBox("Тайминги и Поведение")
        cols = QHBoxLayout()

        col1 = QFormLayout()
        # Позволяем ставить 0.1 сек
        self.delay_min = self.create_spin(self.settings_mgr.get("delay_min"), 0.1, 60)
        self.delay_min.valueChanged.connect(lambda v: self.settings_mgr.set("delay_min", v))
        col1.addRow("Мин. пауза (сек):", self.delay_min)

        self.delay_max = self.create_spin(self.settings_mgr.get("delay_max"), 0.1, 60)
        self.delay_max.valueChanged.connect(lambda v: self.settings_mgr.set("delay_max", v))
        col1.addRow("Макс. пауза (сек):", self.delay_max)

        self.stay_time = self.create_spin(self.settings_mgr.get("page_stay_time"), 0.1, 30)
        self.stay_time.valueChanged.connect(lambda v: self.settings_mgr.set("page_stay_time", v))
        col1.addRow("Чтение страницы (сек):", self.stay_time)

        # Печать: ставим 3 знака после запятой для сверхбыстрого ввода (0.005)
        self.type_min = self.create_spin(self.settings_mgr.get("typing_speed_min"), 0.001, 1.0, decimals=3)
        self.type_min.setSingleStep(0.01)
        self.type_min.valueChanged.connect(lambda v: self.settings_mgr.set("typing_speed_min", v))
        col1.addRow("Печать мин (сек/симв):", self.type_min)

        self.type_max = self.create_spin(self.settings_mgr.get("typing_speed_max"), 0.001, 1.0, decimals=3)
        self.type_max.setSingleStep(0.01)
        self.type_max.valueChanged.connect(lambda v: self.settings_mgr.set("typing_speed_max", v))
        col1.addRow("Печать макс (сек/симв):", self.type_max)

        col2 = QFormLayout()
        self.scroll_mode = AnimatedComboBox()
        self.scroll_mode.setMinimumHeight(35)
        self.scroll_mode.addItems(["smooth", "random", "instant"])
        self.scroll_mode.setCurrentText(self.settings_mgr.get("scroll_mode") or "smooth")
        self.scroll_mode.currentTextChanged.connect(lambda t: self.settings_mgr.set("scroll_mode", t))
        col2.addRow("Режим скролла:", self.scroll_mode)

        # Скролл: Разрешаем большие скачки (до 5000px)
        self.scroll_step_min = self.create_spin(self.settings_mgr.get("scroll_step_min"), 10, 5000, decimals=0, step = 1)
        self.scroll_step_min.valueChanged.connect(lambda v: self.settings_mgr.set("scroll_step_min", int(v)))
        col2.addRow("Скролл Мин (px):", self.scroll_step_min)

        self.scroll_step_max = self.create_spin(self.settings_mgr.get("scroll_step_max"), 10, 5000, decimals=0, step = 1)
        self.scroll_step_max.valueChanged.connect(lambda v: self.settings_mgr.set("scroll_step_max", int(v)))
        col2.addRow("Скролл Макс (px):", self.scroll_step_max)

        # Задержка скролла (микро-паузы)
        self.scroll_delay_min = self.create_spin(self.settings_mgr.get("scroll_delay_min"), 0.001, 1.0, decimals=3)
        self.scroll_delay_min.valueChanged.connect(lambda v: self.settings_mgr.set("scroll_delay_min", v))
        col2.addRow("Пауза скролла Мин:", self.scroll_delay_min)

        self.scroll_delay_max = self.create_spin(self.settings_mgr.get("scroll_delay_max"), 0.001, 1.0, decimals=3)
        self.scroll_delay_max.valueChanged.connect(lambda v: self.settings_mgr.set("scroll_delay_max", v))
        col2.addRow("Пауза скролла Макс:", self.scroll_delay_max)

        cols.addLayout(col1);
        cols.addLayout(col2)
        time_group.setLayout(cols)
        layout.addWidget(time_group)

        # 4. Антидетект
        stealth_group = QGroupBox("Антидетект")
        sl = QVBoxLayout()
        self.check_headless = QCheckBox("Запускать браузер скрыто (Headless)")
        self.check_headless.setChecked(self.settings_mgr.get("headless_mode"))
        self.check_headless.stateChanged.connect(lambda v: self.settings_mgr.set("headless_mode", bool(v)))
        sl.addWidget(self.check_headless)

        self.check_stealth = QCheckBox("Скрывать WebDriver (Stealth)")
        self.check_stealth.setChecked(self.settings_mgr.get("use_stealth"))
        self.check_stealth.stateChanged.connect(lambda v: self.settings_mgr.set("use_stealth", bool(v)))
        sl.addWidget(self.check_stealth)

        self.check_human = QCheckBox("Human Moves (Мышь, Скролл)")
        self.check_human.setChecked(self.settings_mgr.get("use_human_moves"))
        self.check_human.stateChanged.connect(lambda v: self.settings_mgr.set("use_human_moves", bool(v)))
        sl.addWidget(self.check_human)

        stealth_group.setLayout(sl)
        layout.addWidget(stealth_group)

        layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def create_spin(self, val, min_v, max_v, decimals=1, step=1):
        s = QDoubleSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(float(val))
        s.setDecimals(decimals)
        s.setSingleStep(step)
        s.setMinimumHeight(35)
        return s

    def refresh_profiles(self):
        self.profile_combo.blockSignals(True);
        self.profile_combo.clear()
        from core.utils import get_user_data_path
        profiles_dir = get_user_data_path("profiles")
        files = []
        if os.path.exists(profiles_dir):
            files = [f.replace(".json", "") for f in os.listdir(profiles_dir) if f.endswith(".json")]
        self.profile_combo.addItems(files);
        self.profile_combo.blockSignals(False)

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "Новый профиль", "Имя:")
        if ok and name:
            from core.utils import get_user_data_path
            filename = os.path.join(get_user_data_path("profiles"), f"{name}.json")
            if os.path.exists(filename): return QMessageBox.warning(self, "Ошибка", "Существует!")
            self.login_worker = LoginWorker(filename)
            self.login_worker.finished_signal.connect(self.on_login_finished)
            self.login_worker.start()
            QMessageBox.information(self, "Вход", "Войдите в аккаунт.")

    def on_login_finished(self, success, message):
        if success:
            self.refresh_profiles(); QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def delete_profile(self):
        name = self.profile_combo.currentText()
        if name and QMessageBox.question(self, "Удаление", f"Удалить {name}?") == QMessageBox.StandardButton.Yes:
            from core.utils import get_user_data_path
            try:
                os.remove(os.path.join(get_user_data_path("profiles"), f"{name}.json")); self.refresh_profiles()
            except:
                pass