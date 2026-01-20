import sys
import os
import ctypes  # <--- Нужна для фикса иконки в панели задач
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def resource_path(relative_path):
    """Получает путь к ресурсам (работает и при запуске скрипта, и в EXE)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    # 1. Настройка масштаба (High DPI)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

    # === ВАЖНО: Фикс иконки в панели задач Windows ===
    # Windows группирует процессы по ID. По умолчанию это "python".
    # Мы меняем ID на свой уникальный, чтобы Windows считала это отдельной программой.
    if sys.platform == 'win32':
        myappid = 'mycompany.hhbot.automation.v1'  # Любая уникальная строка
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    # 2. Установка иконки
    icon_path = resource_path("resources/app_icon.ico")

    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)  # Иконка окна (слева вверху)
    else:
        print(f"Иконка не найдена по пути: {icon_path}")

    # 3. Стиль Fusion (Обязательно для вашего CSS!)
    app.setStyle(QStyleFactory.create("Fusion"))

    window = MainWindow()

    # Дублируем установку иконки конкретно для главного окна (иногда помогает)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()