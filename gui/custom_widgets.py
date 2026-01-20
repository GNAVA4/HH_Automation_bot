import os
import time
from PyQt6.QtWidgets import (QComboBox, QWidget, QListView)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QEvent, QVariantAnimation, QRectF, QModelIndex

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARROW_PATH = os.path.join(BASE_DIR, "resources", "icons", "arrow.svg").replace('\\', '/')


class AnimatedArrow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.angle = 0
        if os.path.exists(ARROW_PATH):
            self.renderer = QSvgRenderer(ARROW_PATH)
        else:
            self.renderer = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.animation = QVariantAnimation(self)
        self.animation.setDuration(250)
        self.animation.valueChanged.connect(self._update_angle)

    def _update_angle(self, value):
        self.angle = value
        self.update()

    def rotate_to(self, end_angle):
        self.animation.setStartValue(self.angle)
        self.animation.setEndValue(end_angle)
        self.animation.start()

    def paintEvent(self, event):
        if not self.renderer: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        rect = QRectF(-self.width() / 2, -self.height() / 2, self.width(), self.height())
        self.renderer.render(painter, rect)
        painter.end()


# === 1. ОБЫЧНЫЙ СПИСОК (АНИМИРОВАННЫЙ) ===
class AnimatedComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setCursor(Qt.CursorShape.PointingHandCursor)

        self.arrow = AnimatedArrow(self)
        self._last_hide_time = 0
        self.model = QStandardItemModel(self)
        self.setModel(self.model)

        self.setView(QListView())
        view = self.view()

        # === ИСПРАВЛЕНИЕ: УБРАЛИ WA_TranslucentBackground ===
        # Оставляем только Frameless, чтобы убрать системную тень Windows, если она мешает,
        # но фон теперь будет рисоваться через CSS.
        view.window().setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        view.viewport().installEventFilter(self)
        self.lineEdit().installEventFilter(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrow.move(self.width() - 30, (self.height() - self.arrow.height()) // 2)

    def showPopup(self):
        self.arrow.rotate_to(180)
        super().showPopup()

    def hidePopup(self):
        self._last_hide_time = time.time()
        self.arrow.rotate_to(0)
        super().hidePopup()

    def eventFilter(self, widget, event):
        if widget == self.lineEdit() and event.type() == QEvent.Type.MouseButtonPress:
            if self.view().isVisible():
                self.hidePopup()
                return True
            if time.time() - self._last_hide_time < 0.2:
                return True
            self.showPopup()
            return True
        return super().eventFilter(widget, event)


# === 2. СПИСОК С ГАЛОЧКАМИ ===
class CheckableComboBox(AnimatedComboBox):
    def __init__(self, placeholder="Выберите..."):
        super().__init__()
        self.placeholder = placeholder
        self.model.itemChanged.connect(self.update_display_text)
        self.update_display_text()

    def addItem(self, text, data=None):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        item.setData(data if data is not None else text, Qt.ItemDataRole.UserRole)
        self.model.appendRow(item)

    def addItems(self, items_dict):
        if isinstance(items_dict, dict):
            for text, data in items_dict.items(): self.addItem(text, data)
        else:
            for text in items_dict: self.addItem(text, text)

    def get_checked_data(self):
        return [self.model.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.model.rowCount()) if self.model.item(i).checkState() == Qt.CheckState.Checked]

    def set_checked_by_data(self, data_list):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            val = item.data(Qt.ItemDataRole.UserRole)
            item.setCheckState(Qt.CheckState.Checked if val in data_list else Qt.CheckState.Unchecked)
        self.update_display_text()

    def update_display_text(self, *args):
        selected = [self.model.item(i).text() for i in range(self.model.rowCount())
                    if self.model.item(i).checkState() == Qt.CheckState.Checked]

        text = ", ".join(selected) if selected else self.placeholder
        font_metrics = self.lineEdit().fontMetrics()
        elided = font_metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.width() - 40)
        self.lineEdit().setText(elided)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display_text()

    def eventFilter(self, widget, event):
        if widget == self.view().viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            item = self.model.itemFromIndex(index)
            if item:
                new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(new_state)
            return True
        return super().eventFilter(widget, event)