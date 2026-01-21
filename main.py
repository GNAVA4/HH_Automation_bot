import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow
from core.utils import get_resource_path

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

    if sys.platform == 'win32':
        myappid = 'mycompany.hhbot.automation.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    # Иконка приложения
    icon_path = get_resource_path("resources/app_icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    app.setStyle(QStyleFactory.create("Fusion"))

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