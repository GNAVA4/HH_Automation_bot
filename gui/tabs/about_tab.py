from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextBrowser)


class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        text_area = QTextBrowser()
        text_area.setReadOnly(True)
        text_area.setOpenExternalLinks(True)

        text_area.setHtml("""
            <style>
                body { font-family: 'Segoe UI', sans-serif; color: #cdd6f4; }
                h1 { color: #cba6f7; margin-bottom: 5px; font-size: 22pt; }
                h3 { color: #89b4fa; margin-top: 25px; margin-bottom: 10px; font-size: 14pt; }
                li { margin-bottom: 8px; color: #bac2de; font-size: 11pt; }
                b { color: #f9e2af; } /* Золотистый цвет для важных слов */
                .highlight { color: #a6e3a1; font-weight: bold; } 

                .footer { 
                    margin-top: 40px; 
                    text-align: center; 
                    color: #585b70; 
                    font-size: 10pt; 
                }
                a { color: #89b4fa; text-decoration: none; font-weight: bold; }
            </style>

            <h1>🤖 HH Automation Bot <span style="font-size: 14pt; color: #fab387;">v3.5 Beta</span></h1>
            <p style="font-size: 12pt;">Профессиональный инструмент для автоматизации поиска работы, имитирующий действия реального человека.</p>

            <hr style="border: 1px solid #45475a;">

            <h3>⚡ Ключевые возможности:</h3>
            <ul>
                <li><b>Умные авто-отклики:</b> Автоматический поиск вакансий по множеству критериев. Бот умеет листать страницы и пропускать "неудобные" вакансии (тесты).</li>
                <li><b>Умный подбор-резюме:</b> Если у вас несколько резюме, бот будет подбирать наиболее подходящее исходя из названия вакансии.</li>
                <li><b>Персонализация:</b> Подстановка названия компании и вакансии в сопроводительное письмо (переменные <i>{company}</i>, <i>{vacancy}</i>).</li>
                <li><b>Мульти-аккаунт:</b> Одновременная работа с несколькими профилями в разных потоках.</li>
                <li><b>Активность профиля:</b> Автоматическое поднятие резюме и имитация "прогрева" аккаунта через чаты.</li>
                <li><b>Антидетект 3.2:</b> Продвинутая маскировка под Google Chrome, нелинейные движения мыши, плавающий скролл.</li>
            </ul>

            <h3>🛠 Инструкция по запуску:</h3>
            <ol style="font-size: 11pt; color: #bac2de;">
                <li>Перейдите во вкладку <span class="highlight">Настройки</span>. Нажмите <b>"Добавить профиль"</b> и войдите в свой аккаунт HH.ru.</li>
                <li>Перейдите во вкладку <span class="highlight">Отклики</span>. Выберите созданный профиль.</li>
                <li>Настройте фильтры поиска и напишите сопроводительное письмо.</li>
                <li>Нажмите <b>"ЗАПУСТИТЬ РАССЫЛКУ"</b>.</li>
            </ol>

            <hr style="border: 1px solid #45475a; margin-top: 30px;">

            <h3>⚠️ ДИСКЛЕЙМЕР И ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ</h3>
            <p>Данное программное обеспечение разработано исключительно в ознакомительных и образовательных целях.</p>
            <p>Автор не несет ответственности за любые последствия использования данного бота, включая (но не ограничиваясь): временную или вечную блокировку аккаунта на hh.ru, пропуск важных вакансий или некорректную отправку сообщений.</p>
            <p>Используя данную программу, вы соглашаетесь с тем, что делаете это <b>на свой страх и риск</b>. Пожалуйста, соблюдайте лимиты сервиса.</p>

            <div class="footer">
                <p>Исходный код и обновления: <a href="https://github.com/GNAVA4/HH_Automation_bot">GitHub Repository</a></p>
            </div>
        """)

        layout.addWidget(text_area)