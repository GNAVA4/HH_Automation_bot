# core/logger.py
import logging
import sys
import os
import html as _html
from PyQt6.QtCore import QObject, pyqtSignal
from core.utils import get_user_data_path

# Цвета уровней (Catppuccin) для лога в GUI
LEVEL_COLORS = {
    logging.ERROR: "#f38ba8",
    logging.CRITICAL: "#f38ba8",
    logging.WARNING: "#f9e2af",
    logging.INFO: "#a6adc8",
    logging.DEBUG: "#6c7086",
}
SUCCESS_COLOR = "#a6e3a1"
SUCCESS_MARKERS = ("пройден", "отправлен", "успешно", "успех", "сохран", "✓", "завершена", "завершено")


class QLogHandler(logging.Handler, QObject):
    """
    Кастомный обработчик логов.
    Перехватывает сообщения logging и отправляет их в GUI через сигнал (в виде
    цветного HTML по уровню).
    """
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        color = LEVEL_COLORS.get(record.levelno, "#a6adc8")
        # Успешные INFO-события подсвечиваем зелёным
        if record.levelno <= logging.INFO:
            low = str(record.getMessage()).lower()
            if any(m in low for m in SUCCESS_MARKERS):
                color = SUCCESS_COLOR
        safe = _html.escape(msg)
        self.log_signal.emit(f'<span style="color:{color};">{safe}</span>')


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