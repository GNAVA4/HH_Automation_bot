import os

# Путь к корню проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Настройки запуска браузера
HEADLESS_MODE = False  # False = мы видим браузер, True = скрытый режим


CURRENT_VERSION = "3.1"
VERSION_FILE_URL = "https://raw.githubusercontent.com/GNAVA4/HH_Automation_bot/main/version.json"
