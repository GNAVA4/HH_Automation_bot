import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QIcon, QPalette, QColor
from gui.main_window import MainWindow
from core.utils import get_resource_path


def apply_dark_palette(app):
    """Принудительно тёмная палитра — чтобы внешний вид НЕ зависел от темы Windows.
    Покрывает виджеты, которые не полностью стилизованы через QSS."""
    base = QColor("#1e1e2e")
    deep = QColor("#181825")
    surface = QColor("#313244")
    text = QColor("#cdd6f4")
    subtle = QColor("#a6adc8")
    disabled = QColor("#6c7086")
    accent = QColor("#89b4fa")

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, base)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, deep)
    p.setColor(QPalette.ColorRole.AlternateBase, surface)
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#11111b"))
    p.setColor(QPalette.ColorRole.ToolTipText, text)
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.Button, surface)
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.BrightText, QColor("#f38ba8"))
    p.setColor(QPalette.ColorRole.Link, accent)
    p.setColor(QPalette.ColorRole.Highlight, accent)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#11111b"))
    p.setColor(QPalette.ColorRole.PlaceholderText, subtle)

    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
                 QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, base)

    app.setPalette(p)

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

    if sys.platform == 'win32':
        myappid = 'mycompany.hhbot.automation.v3'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    # Иконка приложения
    icon_path = get_resource_path("resources/app_icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    app.setStyle(QStyleFactory.create("Fusion"))
    apply_dark_palette(app)

    window = MainWindow()

    # === ФИКС ИКОНОК В QSS ===
    # Читаем стиль
    style_path = get_resource_path("gui/styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            qss_data = f.read()

        # Получаем АБСОЛЮТНЫЙ путь к папке resources
        # В Windows пути с обратным слэшем, CSS их не любит, меняем на прямой
        res_dir = get_resource_path("resources").replace("\\", "/")

        # Подменяем относительный путь на абсолютный прямо в тексте стилей
        # Было: url(resources/icons/...)
        # Стало: url(C:/Path/To/_internal/resources/icons/...)
        qss_data = qss_data.replace("url(resources", f"url({res_dir}")

        window.setStyleSheet(qss_data)

    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()