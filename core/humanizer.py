import time
import random
import math


class HumanLike:
    def __init__(self, page, engine):
        self.page = page
        self.engine = engine

    def _sleep(self, seconds):
        """Пауза через умный сон движка"""
        self.engine.smart_sleep(seconds)

    def smooth_scroll_to(self, locator):
        if not locator.is_visible(): return

        try:
            box = locator.bounding_box()
            if not box: return

            viewport_h = self.page.viewport_size['height'] if self.page.viewport_size else 800

            # Загружаем скоростные настройки
            s_min = float(self.engine.settings_mgr.get("scroll_step_min"))
            s_max = float(self.engine.settings_mgr.get("scroll_step_max"))
            d_min = float(self.engine.settings_mgr.get("scroll_delay_min"))
            d_max = float(self.engine.settings_mgr.get("scroll_delay_max"))

            if s_min > s_max: s_min = s_max

            steps = 0
            while True:
                self.engine.check_running()

                box = locator.bounding_box()
                if not box: break
                y = box['y']

                if 100 < y < viewport_h - 100: break

                # Более агрессивный скролл
                scroll_amount = random.randint(int(s_min), int(s_max))
                delta = scroll_amount if y > viewport_h else -scroll_amount

                self.page.mouse.wheel(0, delta)
                self._sleep(random.uniform(d_min, d_max))

                steps += 1
                if steps > 50: break
        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e
            try:
                locator.scroll_into_view_if_needed()
            except:
                pass

    def human_type(self, locator, text):
        """Ввод текста с настроенной скоростью"""
        try:
            locator.click()

            t_min = float(self.engine.settings_mgr.get("typing_speed_min"))
            t_max = float(self.engine.settings_mgr.get("typing_speed_max"))

            # Если скорость супер-быстрая (< 0.01), вводим кусками или сразу
            if t_max < 0.01:
                locator.fill(text)
                return

            for char in text:
                self.engine.check_running()

                # Переводим секунды в мс для Playwright
                delay_ms = int(random.uniform(t_min, t_max) * 1000)
                locator.type(char, delay=delay_ms)

                # Редкая задержка, только если скорость "человеческая"
                if t_max > 0.05 and random.random() < 0.02:
                    self._sleep(random.uniform(0.1, 0.4))

        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e
            locator.fill(text)

    def human_click(self, locator):
        try:
            box = locator.bounding_box()
            if box:
                # Меньше лишних движений
                x = box["x"] + box["width"] / 2 + random.uniform(-2, 2)
                y = box["y"] + box["height"] / 2 + random.uniform(-2, 2)
                self.page.mouse.move(x, y)

            # Минимальная пауза перед кликом
            self._sleep(random.uniform(0.05, 0.15))
            locator.click()
        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e
            locator.click()

    def random_scroll(self):
        # Быстрый микро-скролл для вида
        try:
            for _ in range(random.randint(1, 3)):
                self.engine.check_running()
                self.page.mouse.wheel(0, random.randint(300, 800))
                self._sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e