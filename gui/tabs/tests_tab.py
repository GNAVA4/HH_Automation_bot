from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QGroupBox, QScrollArea, QFrame, QFormLayout, QLineEdit,
                             QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QComboBox)
from core.test_solver import load_answers, save_answers


class TestsTab(QWidget):
    """Редактор базы ответов на тесты работодателя (user_data/test_answers.json)."""

    def __init__(self):
        super().__init__()
        self.kb = load_answers()
        self.init_ui()
        self.load_into_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("scroll_content")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel("Ответы на тесты работодателя. Сначала ищется совпадение по «Типовым вопросам» "
                      "(подстрока в тексте вопроса), иначе применяются ответы по умолчанию ниже.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #a6adc8; font-style: italic;")
        layout.addWidget(info)

        # --- Ответы по умолчанию ---
        def_group = QGroupBox("Ответы по умолчанию")
        form = QFormLayout()

        self.salary_edit = QLineEdit()
        form.addRow("Зарплатные ожидания:", self.salary_edit)

        self.yesno_edit = QLineEdit()
        form.addRow("Ответ на вопрос Да/Нет:", self.yesno_edit)

        self.rating_edit = QLineEdit()
        form.addRow("Оценка уровня (текст):", self.rating_edit)

        self.scale_edit = QLineEdit()
        form.addRow("Оценка по шкале (число):", self.scale_edit)

        self.skill_combo = QComboBox()
        self.skill_combo.setMinimumHeight(32)
        self.skill_combo.addItems(["last", "middle", "first"])
        form.addRow("Уровень владения (radio):", self.skill_combo)

        self.open_edit = QPlainTextEdit()
        self.open_edit.setMinimumHeight(80)
        form.addRow("Универсальный ответ\n(открытые вопросы):", self.open_edit)

        def_group.setLayout(form)
        layout.addWidget(def_group)

        # --- Типовые вопросы ---
        qa_group = QGroupBox("Типовые вопросы (фраза в вопросе → ответ)")
        qa_layout = QVBoxLayout()

        hint = QLabel("«Фраза» — подстрока, которую ищем в тексте вопроса (регистр не важен). "
                      "Для выбора варианта укажите его точный текст (напр. «Да»).")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a6adc8;")
        qa_layout.addWidget(hint)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Фраза в вопросе", "Ответ"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(220)
        qa_layout.addWidget(self.table)

        btns = QHBoxLayout()
        btn_add = QPushButton("Добавить строку")
        btn_add.clicked.connect(lambda: self.table.insertRow(self.table.rowCount()))
        btn_del = QPushButton("Удалить выбранное")
        btn_del.clicked.connect(self.delete_selected_row)
        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        btns.addStretch()
        qa_layout.addLayout(btns)

        qa_group.setLayout(qa_layout)
        layout.addWidget(qa_group)

        # --- Сохранение ---
        save_row = QHBoxLayout()
        save_row.addStretch()
        self.btn_save = QPushButton("💾 Сохранить базу")
        self.btn_save.setMinimumHeight(42)
        self.btn_save.clicked.connect(self.save)
        save_row.addWidget(self.btn_save)
        layout.addLayout(save_row)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_into_ui(self):
        fb = self.kb.get("fallbacks", {})
        self.salary_edit.setText(str(fb.get("salary_text", "")))
        self.yesno_edit.setText(str(fb.get("yesno_prefer", "Да")))
        self.rating_edit.setText(str(fb.get("rating_text", "")))
        self.scale_edit.setText(str(fb.get("rating_scale_max", "5")))
        self.open_edit.setPlainText(str(fb.get("open_text", "")))
        idx = self.skill_combo.findText(str(fb.get("skill_level", "last")))
        self.skill_combo.setCurrentIndex(idx if idx >= 0 else 0)

        qa = self.kb.get("qa", [])
        self.table.setRowCount(0)
        for entry in qa:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(entry.get("match", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(entry.get("answer", ""))))

    def delete_selected_row(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def save(self):
        fb = self.kb.setdefault("fallbacks", {})
        fb["salary_text"] = self.salary_edit.text().strip()
        fb["yesno_prefer"] = self.yesno_edit.text().strip() or "Да"
        fb["rating_text"] = self.rating_edit.text().strip()
        fb["rating_scale_max"] = self.scale_edit.text().strip() or "5"
        fb["skill_level"] = self.skill_combo.currentText()
        fb["open_text"] = self.open_edit.toPlainText().strip()

        qa = []
        for r in range(self.table.rowCount()):
            m_item = self.table.item(r, 0)
            a_item = self.table.item(r, 1)
            match = m_item.text().strip() if m_item else ""
            answer = a_item.text().strip() if a_item else ""
            if match:
                qa.append({"match": match, "answer": answer})
        self.kb["qa"] = qa

        if save_answers(self.kb):
            QMessageBox.information(self, "Сохранено", "База ответов сохранена.")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить базу ответов.")
