import json
import os
from core.utils import get_user_data_path

SETTINGS_FILE = get_user_data_path("settings.json")

DEFAULT_SETTINGS = {
    "current_profile": "",
    "openai_api_key": "",
    "limit_applications": 200,  # Подняли лимит, раз мы быстрые
    "limit_messages": 50,
    "enable_multi_account": False,
    "use_stealth": True,
    "use_human_moves": True,

    # === НОВЫЕ СКОРОСТНЫЕ ДЕФОЛТЫ ===
    "headless_mode": False,

    # Паузы между вакансиями (Быстро)
    "delay_min": 1.0,
    "delay_max": 3.0,

    # Печать (Почти мгновенно, как макрос или ctrl+v)
    "typing_speed_min": 0.005,
    "typing_speed_max": 0.05,

    "page_stay_time": 1.0,  # Быстрый взгляд

    # Скролл (Размашистый и быстрый)
    "scroll_mode": "smooth",
    "scroll_step_min": 250,  # Минимальный рывок
    "scroll_step_max": 1200,  # Максимальный рывок
    "scroll_delay_min": 0.005,  # Почти без пауз
    "scroll_delay_max": 0.05,

    "smart_resume": True
}


class SettingsManager:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    # Merge defaults with saved to ensure new keys exist
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except:
                return DEFAULT_SETTINGS
        return DEFAULT_SETTINGS

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()