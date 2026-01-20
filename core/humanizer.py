import time
import random
import math


class HumanLike:
    def __init__(self, page, engine):
        self.page = page
        self.engine = engine  # Ссылка на движок для проверки флага и настроек

    def _sleep(self, seconds):
        """Пауза через умный сон движка"""
        self.engine.smart_sleep(seconds)

    def smooth_scroll_to(self, locator):
        if not locator.is_visible(): return

        try:
            box = locator.bounding_box()
            if not box: return

            viewport_h = self.page.viewport_size['height'] if self.page.viewport_size else 800

            # Загружаем настройки
            s_min = float(self.engine.settings_mgr.get("scroll_step_min"))
            s_max = float(self.engine.settings_mgr.get("scroll_step_max"))

            # Защита от дурака (чтобы min не был больше max)
            if s_min > s_max: s_min = s_max

            steps = 0
            while True:
                self.engine.check_running()

                box = locator.bounding_box()
                if not box: break
                y = box['y']

                if 100 < y < viewport_h - 100: break

                # Рандомная сила скролла
                scroll_amount = random.randint(int(s_min), int(s_max))
                delta = scroll_amount if y > viewport_h else -scroll_amount

                self.page.mouse.wheel(0, delta)
                self._sleep(random.uniform(0.05, 0.15))

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

            # Получаем настройки скорости (в секундах)
            t_min = float(self.engine.settings_mgr.get("typing_speed_min"))
            t_max = float(self.engine.settings_mgr.get("typing_speed_max"))

            for char in text:
                self.engine.check_running()

                # Playwright delay (в мс) - базовый
                # Мы добавим свой sleep для большей хаотичности

                locator.type(char, delay=int(t_min * 1000))  # Базовая задержка из настроек

                # Дополнительная случайная задержка сверху
                extra_sleep = random.uniform(0, t_max - t_min)
                if extra_sleep > 0:
                    self._sleep(extra_sleep)

                # Редкая длинная пауза ("задумался")
                if random.random() < 0.05:
                    self._sleep(random.uniform(0.3, 0.7))

        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e
            locator.fill(text)  # Если не вышло по буквам, вставляем сразу

    def human_click(self, locator):
        try:
            box = locator.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
                self.page.mouse.move(x, y, steps=5)

            self._sleep(random.uniform(0.1, 0.3))
            locator.click()
        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e
            locator.click()

    def random_scroll(self):
        try:
            for _ in range(random.randint(2, 5)):
                self.engine.check_running()
                self.page.mouse.wheel(0, random.randint(100, 400))
                self._sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            if "Stopped" in str(e) or "Target closed" in str(e): raise e