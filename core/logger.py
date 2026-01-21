# core/logger.py
import logging
import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from core.utils import get_user_data_path

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
    logger = logging.getLogger("HH_Automation_bot")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # === ИЗМЕНЕНИЕ ЗДЕСЬ ===
    # Логи сохраняем в AppData/logs
    log_dir = get_user_data_path("logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = logging.FileHandler(os.path.join(log_dir, "app_log.txt"), encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    gui_handler = QLogHandler()
    gui_handler.setFormatter(formatter)
    logger.addHandler(gui_handler)

    return logger, gui_handler