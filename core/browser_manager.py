from playwright.sync_api import sync_playwright
import time
import random
import logging
import json
import os
from urllib.parse import urlencode

from database.db_manager import DBManager
from core.settings_manager import SettingsManager
from core.humanizer import HumanLike
from core.config import HEADLESS_MODE
from core.utils import get_user_data_path, get_resource_path

logger = logging.getLogger("HH_Automation_bot")


class BrowserEngine:
    def __init__(self, profile_name=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.human = None
        self.should_run = True

        self.settings_mgr = SettingsManager()
        self.profile_name = profile_name if profile_name else self.settings_mgr.get("current_profile")
        self.db = DBManager()

        try:
            # Локаторы вшиты в EXE, берем через get_resource_path
            with open(get_resource_path("resources/locators.json"), "r") as f:
                self.locators = json.load(f)
        except:
            self.locators = {}

    def log(self, message, level="info"):
        msg = f"[{self.profile_name}] {message}"
        if level == "info":
            logger.info(msg)
        elif level == "warning":
            logger.warning(msg)
        elif level == "error":
            logger.error(msg)

    def stop_execution(self):
        self.should_run = False
        # Не закрываем контекст здесь, чтобы избежать greenlet error.
        # Поток остановится при проверке check_running.

    def check_running(self):
        if not self.should_run:
            raise InterruptedError("Stopped by button")

    def smart_sleep(self, seconds):
        """
        Умный сон с проверкой флага остановки.
        Поддерживает микро-задержки меньше 0.1 сек.
        """
        end_time = time.time() + seconds
        while True:
            self.check_running()
            remaining = end_time - time.time()

            if remaining <= 0:
                break

            # Спим либо 0.1 сек (для проверки стопа), либо остаток времени, если он меньше
            time.sleep(min(0.1, remaining))

    def start_browser(self):
        self.log("Запуск браузера...")
        self.playwright = sync_playwright().start()

        # Получаем настройку
        is_headless = self.settings_mgr.get("headless_mode")

        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            # "--start-maximized", <--- ЭТО ТЕПЕРЬ ЗАВИСИТ ОТ РЕЖИМА
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-zygote",
            "--hide-scrollbars",
            "--mute-audio",
        ]



        self.browser = self.playwright.chromium.launch(
            headless=is_headless,
            args=args,
            channel="chrome",
            ignore_default_args=["--enable-automation"]
        )
        profile_name = self.settings_mgr.get("current_profile")

        # Профили лежат в AppData/profiles
        profiles_dir = get_user_data_path("profiles")
        if not os.path.exists(profiles_dir): os.makedirs(profiles_dir)

        state_path = os.path.join(profiles_dir, f"{self.profile_name}.json")
        state_path = os.path.abspath(state_path)  # На всякий случай нормализуем

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

        # Настройка вьюпорта
        if is_headless:
            # В скрытом режиме нужно жесткое разрешение
            viewport = {'width': 1920, 'height': 1080}
        else:
            # В видимом - null, чтобы подстроился под окно
            viewport = None

        context_options = {
            "viewport": viewport,
            "user_agent": user_agent,
            "locale": "ru-RU",
            "timezone_id": "Europe/Moscow",
            "permissions": ["geolocation", "notifications"]
        }

        if os.path.exists(state_path):
            self.log(f"Загрузка куки: {state_path}")
            context_options["storage_state"] = state_path
        else:
            self.log(f"Файл куки не найден: {state_path}", "warning")

        self.context = self.browser.new_context(**context_options)
        self.page = self.context.new_page()

        if self.settings_mgr.get("use_stealth") is not False:
            self._enable_stealth(self.page)

        self.human = HumanLike(self.page, self)

    def _enable_stealth(self, page):
        page.add_init_script(
            "if (Object.getPrototypeOf(navigator).hasOwnProperty('webdriver')) { delete Object.getPrototypeOf(navigator).webdriver; }")
        page.add_init_script("window.chrome = { runtime: {} };")
        page.add_init_script("Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });")

    def run_search(self, data):
        if not self.page: return
        base_url = "https://hh.ru/search/vacancy"
        query_params = []

        query_params.append(("text", data.get('text', '')))
        excl = data.get('excluded_text', '')
        if excl: query_params.append(("excluded_text", excl))
        if data.get('salary'):
            query_params.append(("salary", data.get('salary')))
            query_params.append(("only_with_salary", "true"))

        area_map = {"Москва": "1", "Санкт-Петербург": "2", "Все регионы": "113"}
        query_params.append(("area", area_map.get(data.get('area'), "113")))
        query_params.append(("items_on_page", "100"))

        for key in ['work_format', 'employment_form', 'experience', 'education', 'label']:
            for val in data.get(key, []): query_params.append((key, val))

        full_url = f"{base_url}?{urlencode(query_params)}"
        self.log(f"Поиск: {full_url}")

        try:
            self.page.goto(full_url)
            self.page.wait_for_load_state("domcontentloaded")
            self.smart_sleep(3)
            self.process_vacancies_loop(data)
        except Exception as e:
            # Пробрасываем закрытие наверх
            if isinstance(e, InterruptedError): raise e
            if "Target closed" in str(e) or "browser has been closed" in str(e): raise e
            self.log(f"Ошибка поиска: {e}", "error")

    def _try_close_chat(self):
        try:
            close_btn = self.page.locator(self.locators["activity"]["chat_close_btn"])
            if close_btn.is_visible():
                self.log("Закрываю всплывший чат...")
                close_btn.click(force=True)
                self.smart_sleep(1)
                return True
        except:
            pass
        return False

    def process_vacancies_loop(self, data):
        limit = self.settings_mgr.get("limit_applications") or 50
        count_processed = 0
        use_human = self.settings_mgr.get("use_human_moves")

        while count_processed < limit:
            self.check_running()
            try:
                # Получаем список вакансий
                all_vacancies = self.page.locator(self.locators["search_page"]["vacancy_card"]).all()
            except Exception as e:
                # ЕСЛИ ОШИБКА ЗДЕСЬ -> БРАУЗЕР ЗАКРЫТ
                if "Target closed" in str(e) or "browser has been closed" in str(e):
                    raise e
                break

            self.log(f"Найдено: {len(all_vacancies)}")
            if not all_vacancies: break

            for vacancy in all_vacancies:
                self.check_running()
                if count_processed >= limit: break

                try:
                    if use_human and self.human:
                        self.human.smooth_scroll_to(vacancy)
                    else:
                        vacancy.scroll_into_view_if_needed()

                    title_el = vacancy.locator("a[data-qa='serp-item__title']").first
                    company_el = vacancy.locator("a[data-qa='vacancy-serp__vacancy-employer']").first
                    title = title_el.text_content() if title_el.is_visible() else "Vacancy"
                    company = company_el.text_content().replace('\u00a0', ' ') if company_el.is_visible() else "Company"
                    url = title_el.get_attribute("href") if title_el.is_visible() else ""

                    apply_btn = vacancy.locator(self.locators["search_page"]["apply_button"]).first
                    if not apply_btn.is_visible(): continue

                    self.log(f"[{count_processed + 1}/{limit}] {title} ({company})")

                    self._try_close_chat()
                    self.smart_sleep(random.uniform(1.0, 1.5))
                    apply_btn.click()

                    is_modal = False
                    try:
                        self.page.wait_for_selector("div[role='dialog']", timeout=3000)
                        is_modal = True
                    except:
                        if self._try_close_chat():
                            try:
                                apply_btn.click(force=True)
                                self.page.wait_for_selector("div[role='dialog']", timeout=3000)
                                is_modal = True
                            except:
                                is_modal = False

                    if is_modal:
                        info = {"title": title, "company": company}
                        if self.handle_response_modal(data, info):
                            self.db.add_application(title, company, url, self.profile_name)
                            count_processed += 1
                            self.smart_sleep(1)
                            self._try_close_chat()
                    else:
                        self.log("Тест/Редирект. Пропуск.", "warning")
                        if "hh.ru/search" not in self.page.url:
                            self.page.go_back()
                            self.page.wait_for_load_state("domcontentloaded")
                            self.smart_sleep(2)

                    self.smart_sleep(random.uniform(2.0, 4.0))

                except Exception as e:
                    if isinstance(e, InterruptedError): raise e
                    # ВАЖНО: Пробрасываем ошибку закрытия
                    if "Target closed" in str(e) or "browser has been closed" in str(e): raise e

                    self.log(f"Ошибка: {e}", "error")
                    try:
                        self.page.keyboard.press("Escape")
                    except:
                        pass

            if count_processed < limit:
                try:
                    next_btn = self.page.locator(self.locators["search_page"]["pager_next"]).first
                    if next_btn.is_visible():
                        self.log("След. страница >>")
                        if use_human and self.human:
                            self.human.smooth_scroll_to(next_btn)
                            self.check_running()
                        self.smart_sleep(1)
                        next_btn.click()
                        self.page.wait_for_load_state("domcontentloaded")
                        self.smart_sleep(3)
                    else:
                        self.log("Конец списка.")
                        break
                except Exception as e:
                    if isinstance(e, InterruptedError): raise e
                    # ВАЖНО: Пробрасываем ошибку закрытия
                    if "Target closed" in str(e) or "browser has been closed" in str(e): raise e
                    break

    def handle_response_modal(self, data, info):
        try:
            modal = self.page.locator("div[role='dialog']")
            target = data.get("resume_name", "").strip().lower()
            if target:
                curr_header = modal.locator("[data-qa='resume-title']").first
                if curr_header.is_visible():
                    curr_text = curr_header.text_content().strip().lower()
                    if target not in curr_text:
                        self.log(f"Смена резюме: {curr_text} -> {target}")
                        curr_header.click(force=True)
                        self.smart_sleep(1.5)
                        options = self.page.locator("[data-magritte-select-option]").all()
                        found = False
                        for opt in options:
                            try:
                                txt = opt.text_content().strip().lower()
                            except:
                                continue
                            if target in txt:
                                opt.scroll_into_view_if_needed()
                                opt.click(force=True)
                                found = True
                                self.smart_sleep(1)
                                break
                        if not found: curr_header.click(force=True)

            text = data.get("cover_letter", "")
            if text:
                final_text = text.replace("{company}", info['company']).replace("{vacancy}", info['title']).replace(
                    "{name}", self.profile_name)
                area = modal.locator("textarea").first
                btn = modal.locator("[data-qa='add-cover-letter']").first
                if not area.is_visible() and btn.is_visible(): btn.click(); self.smart_sleep(0.5)
                if area.is_visible():
                    if self.human and self.settings_mgr.get("use_human_moves"):
                        self.human.human_type(area, final_text)
                    else:
                        area.fill(final_text)

            submit = modal.locator("[data-qa='vacancy-response-submit-popup']").first
            if not submit.is_visible(): submit = modal.locator("button[type='submit']").first
            if submit.is_visible():
                submit.click()
                try:
                    modal.wait_for(state="hidden", timeout=5000); return True
                except:
                    return False
        except:
            return False
        return False

    def run_resume_update(self):
        self.log("=== ПОДНЯТИЕ РЕЗЮМЕ ===")
        try:
            self.page.goto("https://hh.ru/applicant/resumes?hhtmFrom=main&hhtmFromLabel=header")
            self.page.wait_for_load_state("domcontentloaded")
            self.smart_sleep(3)

            while True:
                self.check_running()
                try:
                    all_buttons = self.page.locator(self.locators["activity"]["resume_update_btn"]).all()
                except Exception as e:
                    # ВАЖНО: Проверка закрытия
                    if "Target closed" in str(e) or "browser has been closed" in str(e): raise e
                    break

                button_to_click = None
                for btn in all_buttons:
                    if not btn.is_visible(): continue
                    txt = btn.text_content().lower()
                    if "поднять" in txt and "автоматически" not in txt:
                        button_to_click = btn
                        break

                if not button_to_click:
                    self.log("Больше нет резюме для поднятия.")
                    break

                self.log("Поднимаю резюме...")
                button_to_click.scroll_into_view_if_needed()
                button_to_click.click()
                self.smart_sleep(2)
                close_btn = self.page.locator(self.locators["activity"]["resume_modal_close"])
                if close_btn.is_visible(): close_btn.click(); self.smart_sleep(1)
                self.smart_sleep(2)

        except Exception as e:
            if isinstance(e, InterruptedError): raise e
            if "Target closed" in str(e) or "browser has been closed" in str(e): raise e
            self.log(f"Ошибка резюме: {e}", "error")

    def run_chat_activity(self, settings):
        try:
            if "hh.ru" not in self.page.url: self.page.goto("https://hh.ru")

            try:
                self.page.locator(self.locators["activity"]["chat_open_btn"]).click(force=True)
            except:
                self.log("Кнопка чатов не найдена", "error"); return

            iframe_sel = self.locators["activity"]["chat_iframe"]
            try:
                self.page.wait_for_selector(iframe_sel, timeout=10000)
            except:
                self.log("Iframe не открылся", "error"); return
            frame = self.page.frame_locator(iframe_sel)

            list_sel = self.locators["activity"]["chat_list_item"]
            try:
                frame.locator(list_sel).first.wait_for(timeout=10000)
            except:
                self.log("Чат пуст", "warning"); return

            limit = settings["max_employers"]
            processed = 0
            use_human = self.settings_mgr.get("use_human_moves")

            while processed < limit:
                self.check_running()
                rows = frame.locator(list_sel).all()
                if processed >= len(rows): break
                row = rows[processed]
                try:
                    row.click();
                    self.smart_sleep(3)
                    try:
                        employer_name = frame.locator(".title--jaEO2q2if2IOwiyO").first.text_content()
                    except:
                        employer_name = "HR"

                    input_area = frame.locator(self.locators["activity"]["chat_input"])
                    if not input_area.is_visible():
                        back = frame.locator(self.locators["activity"]["chat_back_btn"])
                        if back.is_visible(): back.click()
                        processed += 1;
                        continue

                    pool = list(settings["messages"])
                    count = min(settings["msgs_per_hr"], len(pool))
                    if count > 0:
                        to_send = random.sample(pool, count)
                        self.log(f"Диалог: {employer_name}")
                        for msg in to_send:
                            self.check_running()
                            if use_human and self.human:
                                self.human.human_type(input_area, msg)
                            else:
                                input_area.fill(msg)
                            self.smart_sleep(0.5)
                            send = frame.locator(self.locators["activity"]["chat_send_btn"])
                            if send.is_visible(): send.click(force=True); self.smart_sleep(2)

                    back = frame.locator(self.locators["activity"]["chat_back_btn"])
                    if back.is_visible(): back.click()
                    processed += 1
                except Exception as e:
                    if isinstance(e, InterruptedError): raise e
                    if "Target closed" in str(e) or "browser has been closed" in str(e): raise e
                    processed += 1
        except Exception as e:
            if isinstance(e, InterruptedError): raise e
            if "Target closed" in str(e) or "browser has been closed" in str(e): raise e

    def stop_browser(self):
        try:
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()
        except:
            pass