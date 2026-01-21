import json
import os
from core.utils import get_user_data_path

SETTINGS_FILE = get_user_data_path("settings.json")

DEFAULT_SETTINGS = {
    "current_profile": "",
    "openai_api_key": "",
    "limit_applications": 50,
    "limit_messages": 20,
    "enable_multi_account": False,
    "use_stealth": True,
    "use_human_moves": True,

    # === НОВОЕ: Скрытый режим ===
    "headless_mode": False,

    # Тайминги
    "delay_min": 3.0,
    "delay_max": 6.0,

    # Печать
    "typing_speed_min": 0.05,
    "typing_speed_max": 0.20,
    "page_stay_time": 3.0,

    # Скролл
    "scroll_mode": "smooth",
    "scroll_step_min": 100,
    "scroll_step_max": 300,
    "scroll_delay_min": 0.05,
    "scroll_delay_max": 0.15
}


class SettingsManager:
    def __init__(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
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