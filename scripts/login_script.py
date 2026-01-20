# login_script.py
from playwright.sync_api import sync_playwright
import time


def save_session():
    with sync_playwright() as p:
        # Запускаем браузер в видимом режиме
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(">>> Перехожу на страницу входа...")
        page.goto("https://hh.ru/account/login")

        print(">>> ПОЖАЛУЙСТА, ВОЙДИТЕ В АККАУНТ ВРУЧНУЮ.")
        print(">>> У вас есть 120 секунд.")
        print(">>> Как только войдете (увидите свое имя или главную страницу), ничего не закрывайте.")

        # Ждем, пока пользователь войдет.
        # Можно просто дать тайм-аут или проверять url
        try:
            # Ждем появления иконки профиля (признак успешного входа)
            # Селектор может отличаться, но обычно data-qa="mainmenu_applicantProfile" работает
            page.wait_for_url ("https://hh.ru/", timeout=60000)
            print(">>> Успешный вход обнаружен!")
        except:
            print(">>> Время истекло или элемент не найден. Сохраняю как есть...")

        # Сохраняем состояние (куки, localStorage) в файл
        context.storage_state(path="user_state.json")
        print(">>> Сессия сохранена в файл 'user_state.json'")

        browser.close()


if __name__ == "__main__":
    save_session()