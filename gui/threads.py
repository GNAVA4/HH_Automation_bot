from PyQt6.QtCore import QThread, pyqtSignal
from core.browser_manager import BrowserEngine
import logging
import os
import time

logger = logging.getLogger("HH_Automation_bot")


class SearchWorker(QThread):
    finished_signal = pyqtSignal(str, str)

    def __init__(self, search_data, profile_name):
        super().__init__()
        self.search_data = search_data
        self.profile_name = profile_name
        self.engine = None

    def run(self):
        status = "finished"
        try:
            time.sleep(0.5)
            self.engine = BrowserEngine(self.profile_name)
            self.engine.start_browser()
            self.engine.run_search(self.search_data)

        except BaseException as e:
            err = str(e)
            # Ловим все вариации ошибки закрытия
            if "Stopped by button" in err:
                status = "stopped"
            elif "ManualClose" in err or "Target closed" in err or "browser has been closed" in err:
                status = "closed_by_user"
                logger.warning(f"[{self.profile_name}] Обнаружено ручное закрытие.")
            else:
                status = f"error: {err}"
                logger.error(f"[{self.profile_name}] CRITICAL: {err}")
        finally:
            if self.engine:
                try:
                    self.engine.stop_browser()
                except:
                    pass
            self.finished_signal.emit(status, self.profile_name)

    def stop(self):
        if self.engine: self.engine.stop_execution()


class ActivityWorker(QThread):
    finished_signal = pyqtSignal(str, str)

    def __init__(self, settings, profile_name):
        super().__init__()
        self.settings = settings
        self.profile_name = profile_name
        self.engine = None

    def run(self):
        status = "finished"
        try:
            time.sleep(0.5)
            self.engine = BrowserEngine(self.profile_name)
            self.engine.start_browser()

            if self.settings["use_chat"]:
                self.engine.run_chat_activity(self.settings)

            if self.settings["use_resume"]:
                self.engine.run_resume_update()

        except BaseException as e:
            err = str(e)
            if "Stopped by button" in err:
                status = "stopped"
            elif "ManualClose" in err or "Target closed" in err or "browser has been closed" in err:
                status = "closed_by_user"
                logger.warning(f"[{self.profile_name}] Обнаружено ручное закрытие.")
            else:
                status = f"error: {err}"
                logger.error(f"[{self.profile_name}] CRITICAL: {err}")
        finally:
            if self.engine:
                try:
                    self.engine.stop_browser()
                except:
                    pass
            self.finished_signal.emit(status, self.profile_name)

    def stop(self):
        if self.engine: self.engine.stop_execution()


class LoginWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, save_path):
        super().__init__()
        self.save_path = save_path

    def run(self):
        from playwright.sync_api import sync_playwright

        logger.info("Запуск мастера авторизации...")
        logger.info("У вас есть 120 секунд, что бы войти в аккаунт...")
        with sync_playwright() as p:
            args = ["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            browser = p.chromium.launch(headless=False, args=args, channel="chrome")

            context = browser.new_context(viewport=None, device_scale_factor=1)
            page = context.new_page()

            success = False
            msg = "Время вышло (120 сек)."

            try:
                # 1. Переход (не ждем полной загрузки вечно)
                try:
                    page.goto("https://hh.ru/account/login", wait_until="domcontentloaded", timeout=15000)
                except:
                    logger.warning("Страница загружается долго, но продолжаем ожидание входа...")

                logger.info("Жду входа в аккаунт...")

                # 2. Цикл ожидания входа (120 сек)
                start = time.time()
                while time.time() - start < 120:
                    if page.is_closed():
                        msg = "Закрыто пользователем"
                        break

                    # Проверяем наличие иконки профиля (значит вошли)
                    # Используем count(), чтобы не падало с ошибкой, если нет
                    try:
                        if page.locator("[data-qa='vacancy-serp__vacancy_response']").count() > 0:
                            success = True
                            msg = f"Профиль успешно сохранен: {os.path.basename(self.save_path)}"
                            logger.info(f"Профиль успешно сохранен: {os.path.basename(self.save_path)}")
                            break

                        # Альтернативная проверка: Кнопка "Создать резюме" или "Мои резюме"
                        if page.locator("[data-qa='mainmenu_myResumes']").count() > 0:
                            success = True
                            msg = f"Профиль успешно сохранен!"
                            logger.info(f"Профиль успешно сохранен: {os.path.basename(self.save_path)}")
                            break

                    except:
                        pass

                    time.sleep(1)

                if success:
                    # Даем время на запись куки
                    time.sleep(3)
                    # Используем переданный save_path, он уже должен быть абсолютным
                    # (он формируется в settings_tab через get_user_data_path)

                    # Для надежности выведем в консоль, куда сохраняем
                    abs_path = os.path.abspath(self.save_path)
                    logger.info(f"Saving cookies to {abs_path}")

                    context.storage_state(path=abs_path)

            except Exception as e:
                msg = f"Ошибка процесса: {e}"
                logger.error(msg)
            finally:
                try:
                    browser.close()
                except:
                    pass
                self.finished_signal.emit(success, msg)


class UpdateWorker(QThread):
    finished_signal = pyqtSignal(dict)  # Возвращает данные json или пустой dict при ошибке

    def run(self):
        import urllib.request
        import json
        from core.config import VERSION_FILE_URL

        try:
            # Запрос к GitHub (таймаут 5 сек)
            with urllib.request.urlopen(VERSION_FILE_URL, timeout=5) as url:
                data = json.loads(url.read().decode())
                self.finished_signal.emit(data)
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {e}")
            self.finished_signal.emit({})