from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from playwright.sync_api import sync_playwright
import os


class TestWorker(QThread):
    finished_signal = pyqtSignal(str)

    def run(self):
        with sync_playwright() as p:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--hide-scrollbars",
                "--mute-audio",
            ]

            browser = p.chromium.launch(
                headless=True,
                args=args,
                channel="chrome",
                ignore_default_args=["--enable-automation"]
            )

            # Используем UserAgent как в основном боте
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=user_agent,
                locale="ru-RU",
                timezone_id="Europe/Moscow"
            )
            page = context.new_page()

            # === ВНЕДРЯЕМ ОБНОВЛЕННЫЙ СТЕЛС ===

            # 1. Удаляем webdriver из прототипа
            page.add_init_script(
                "if (Object.getPrototypeOf(navigator).hasOwnProperty('webdriver')) { delete Object.getPrototypeOf(navigator).webdriver; }")

            # 2. Плагины с правильным прототипом
            page.add_init_script("""
                (function () {
                    const makePluginArray = (plugins) => {
                        const pluginArray = plugins.map((p) => {
                            const plugin = Object.create(Plugin.prototype);
                            Object.defineProperty(plugin, 'name', { value: p.name });
                            Object.defineProperty(plugin, 'filename', { value: p.filename });
                            Object.defineProperty(plugin, 'description', { value: p.description });
                            return plugin;
                        });
                        Object.setPrototypeOf(pluginArray, PluginArray.prototype);
                        return pluginArray;
                    };
                    const fakePlugins = makePluginArray([
                        { name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                        { name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "" },
                        { name: "Native Client", filename: "internal-nacl-plugin", description: "" }
                    ]);
                    Object.defineProperty(navigator, 'plugins', { get: () => fakePlugins });
                    Object.defineProperty(navigator, 'mimeTypes', { 
                        get: () => { const m = []; Object.setPrototypeOf(m, MimeTypeArray.prototype); return m; } 
                    });
                })();
            """)

            # 3. Chrome Runtime
            page.add_init_script("window.chrome = { runtime: {} };")

            try:
                page.goto("https://bot.sannysoft.com/")
                page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass

            path = "diagnosis_result.png"
            page.screenshot(path=path, full_page=True)
            browser.close()

            self.finished_signal.emit(path)


class DiagnosticsTab(QWidget):
    # ... (Весь класс UI оставляем без изменений, как в прошлом ответе) ...
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel("Нажмите кнопку, чтобы проверить маскировку бота.")
        layout.addWidget(self.label)
        self.btn = QPushButton("Запустить тест (SannySoft)")
        self.btn.clicked.connect(self.run_test)
        self.btn.setMinimumHeight(50)
        layout.addWidget(self.btn)
        scroll = QScrollArea()
        self.image_label = QLabel("Здесь будет результат")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

    def run_test(self):
        self.btn.setEnabled(False)
        self.btn.setText("Выполняется проверка...")
        self.label.setText("Перехожу на bot.sannysoft.com...")
        self.worker = TestWorker()
        self.worker.finished_signal.connect(self.show_result)
        self.worker.start()

    def show_result(self, path):
        self.btn.setEnabled(True)
        self.btn.setText("Запустить тест (SannySoft)")
        self.label.setText("Результат проверки:")
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(True)
        else:
            self.image_label.setText("Ошибка: скриншот не создан.")