# core/logger.py
import logging
import sys
from PyQt6.QtCore import QObject, pyqtSignal
import os

class QLogHandler(logging.Handler, QObject):
    """
    Кастомный обработчик логов.
    Перехватывает сообщения logging и отправляет их в GUI через сигнал.
    Наследуется от QObject, чтобы иметь возможность испускать сигналы.
    """
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        # Отправляем текст в интерфейс
        self.log_signal.emit(msg)

def setup_logger():
    """
    Настройка глобального логгера приложения.
    Возвращает объект logger и handler для подключения к GUI.
    """
    logger = logging.getLogger("HH_Bot")
    logger.setLevel(logging.DEBUG) # Ловим все сообщения (INFO, DEBUG, ERROR)

    # 1. Формат сообщений: [Время] [Уровень]: Сообщение
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')

    # 2. Вывод в консоль (для разработчика)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 3. Вывод в файл (чтобы история сохранялась)
    file_handler = logging.FileHandler(os.path.join("logs", "app_log.txt"), encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 4. Вывод в GUI (создаем наш кастомный хендлер)
    gui_handler = QLogHandler()
    gui_handler.setFormatter(formatter)
    logger.addHandler(gui_handler)

    return logger, gui_handler