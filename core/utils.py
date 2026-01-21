import sys
import os


def get_base_path():
    """Возвращает абсолютный путь к папке приложения."""
    if getattr(sys, 'frozen', False):
        # Если EXE - папка, где лежит exe файл
        base = os.path.dirname(sys.executable)
    else:
        # Если скрипт - корень проекта
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.abspath(base)


def get_user_data_path(filename=""):
    """
    Путь к папке user_data (рядом с exe).
    Возвращает АБСОЛЮТНЫЙ путь.
    """
    base = get_base_path()
    data_dir = os.path.join(base, "user_data")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return os.path.join(data_dir, filename)


def get_resource_path(relative_path):
    """
    Путь к ресурсам (_internal или корень).
    Возвращает АБСОЛЮТНЫЙ путь.
    """
    if getattr(sys, 'frozen', False):
        # В EXE (onedir) ресурсы лежат в _internal
        base_path = os.path.join(sys._MEIPASS)
    else:
        base_path = get_base_path()

    return os.path.join(base_path, relative_path)