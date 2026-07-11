"""
Алгоритмический решатель тестов работодателя на hh.ru (без LLM).

Модель страницы теста (проверено на реальных вакансиях):
  - маркер теста:            [data-qa='employer-asking-for-test']
  - вопрос = пара по индексу: [data-qa='task-question'] (текст) <-> [data-qa='task-body'] (ответ)
  - варианты выбора:          label[data-qa='cell'] внутри task-body (клик по label выбирает radio/checkbox)
  - свободный ответ:          textarea внутри task-body
  - кнопка отправки:          [data-qa='vacancy-response-submit-popup']

База ответов правится пользователем (вкладка "Тесты") в user_data/test_answers.json.
"""
import json
import os
import re
import logging

from core.utils import get_user_data_path

logger = logging.getLogger("HH_Automation_bot")

ANSWERS_FILE = "test_answers.json"

DEFAULT_KB = {
    # Список правил пользователя: подстрока вопроса -> готовый ответ
    # Для radio ответ = текст варианта ("Да"), для textarea = сам текст.
    "qa": [],
    "fallbacks": {
        "salary_text": "по договоренности",
        "open_text": "Благодарю за интерес к моей кандидатуре. Готов подробно рассказать "
                     "об опыте и ответить на все вопросы на собеседовании.",
        "yesno_prefer": "Да",
        "rating_text": "Высокий уровень",   # ответ на текстовый вопрос «как оцениваете уровень…»
        "rating_scale_max": "5",             # ответ, если в вопросе явная шкала (1..5)
        "skill_level": "last"   # last | first | middle — какой вариант шкалы владения выбирать
    }
}

# Ключевые слова для классификации свободных вопросов
SALARY_KEYWORDS = ["зарплат", "заработн", "доход", "оклад", "ндфл", "вилк", "ожидания по уровню", "уровень дохода"]
# Свободный вопрос, который по смыслу «да/нет» -> отвечаем утвердительно
YESNO_TEXT_KEYWORDS = ["есть ли", "имеется ли", "имеете ли", "владеете ли", "готовы ли", "готов ли",
                       "можете ли", "согласны ли", "рассматриваете ли", "устраивает ли", "подходит ли",
                       "есть высшее", "наличие ", "знаком ли", "знакомы ли"]
# Свободный вопрос про самооценку уровня
RATING_TEXT_KEYWORDS = ["как оцениваете", "как вы оцениваете", "оцените", "оценка", "уровень знаний",
                        "по шкале", "оцени свой уровень", "оцени уровень"]
SCALE_MARKERS = ["по шкале", "от 1 до 5", "от 1 до 10", "1-5", "1-10", "от 0 до"]
# Варианты, которые нельзя выбирать «по максимуму»
CUSTOM_OPTIONS = ["свой вариант", "другое", "свой ответ", "иное", "затрудняюсь"]
NEGATIVE_OPTIONS = ["не владею", "нет опыта", "не имею"]


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").replace(" ", " ").strip().lower())


def get_answers_path():
    return get_user_data_path(ANSWERS_FILE)


def load_answers():
    """Загружает базу ответов, дополняя недостающие поля дефолтами.
    Если файла нет — создаёт заготовку. Используется и солвером, и вкладкой 'Тесты'."""
    path = get_answers_path()
    kb = json.loads(json.dumps(DEFAULT_KB))  # глубокая копия
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user.get("qa"), list):
                kb["qa"] = user["qa"]
            if isinstance(user.get("fallbacks"), dict):
                kb["fallbacks"].update(user["fallbacks"])
        except Exception as e:
            logger.warning(f"TestSolver: не удалось прочитать {ANSWERS_FILE}: {e}")
    else:
        save_answers(kb)
    return kb


def save_answers(kb):
    try:
        with open(get_answers_path(), "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"TestSolver: не удалось сохранить {ANSWERS_FILE}: {e}")
        return False


class TestSolver:
    def __init__(self, engine=None):
        self.engine = engine
        self.kb = self.load_kb()

    # ---------- База ответов ----------
    def load_kb(self):
        return load_answers()

    # ---------- Детект и разбор ----------
    def has_test(self, page):
        try:
            return page.locator("[data-qa='employer-asking-for-test']").count() > 0
        except Exception:
            return False

    def parse(self, page):
        """Возвращает список вопросов: {index, question, type, options}."""
        questions = []
        bodies = page.locator("[data-qa='task-body']")
        try:
            n = bodies.count()
        except Exception:
            n = 0
        for i in range(n):
            body = bodies.nth(i)
            try:
                qtext = body.locator("[data-qa='task-question']").first.text_content() or ""
            except Exception:
                qtext = ""
            try:
                radios = body.locator("input[type='radio']").count()
                checks = body.locator("input[type='checkbox']").count()
                areas = body.locator("textarea").count()
            except Exception:
                radios = checks = areas = 0

            options = []
            if radios or checks:
                cells = body.locator("label[data-qa='cell']")
                try:
                    cn = cells.count()
                except Exception:
                    cn = 0
                for c in range(cn):
                    try:
                        options.append((cells.nth(c).text_content() or "").strip())
                    except Exception:
                        options.append("")

            if checks:
                qtype = "checkbox"
            elif radios:
                qtype = "radio"
            elif areas:
                qtype = "textarea"
            else:
                qtype = "unknown"

            questions.append({"index": i, "question": qtext.strip(), "type": qtype, "options": options})
        return questions

    # ---------- Логика ответа ----------
    def decide(self, q):
        """Возвращает строку-ответ: текст варианта (для выбора) или текст (для textarea)."""
        qn = _norm(q["question"])

        # 1. Пользовательская база — приоритет
        for entry in self.kb.get("qa", []):
            m = _norm(entry.get("match", ""))
            if m and m in qn:
                return entry.get("answer", "")

        # 2. Свободный ввод — классифицируем по смыслу, но НИКОГДА не возвращаем пусто
        if q["type"] == "textarea":
            if any(k in qn for k in SALARY_KEYWORDS):
                return self.kb["fallbacks"].get("salary_text") or "по договоренности"
            if any(k in qn for k in YESNO_TEXT_KEYWORDS):
                return self.kb["fallbacks"].get("yesno_prefer") or "Да"
            if any(k in qn for k in RATING_TEXT_KEYWORDS):
                if any(m in qn for m in SCALE_MARKERS):
                    return self.kb["fallbacks"].get("rating_scale_max") or "5"
                return self.kb["fallbacks"].get("rating_text") or "Высокий уровень"
            return self.kb["fallbacks"].get("open_text") or "Готов обсудить детали на собеседовании."

        # 3. Выбор варианта
        if q["type"] in ("radio", "checkbox"):
            opts = q["options"]
            norms = [_norm(o) for o in opts]
            prefer = _norm(self.kb["fallbacks"].get("yesno_prefer", "да"))

            # Да/Нет: точное совпадение, затем "да..."
            for o, nz in zip(opts, norms):
                if nz == prefer:
                    return o
            for o, nz in zip(opts, norms):
                if prefer and nz.startswith(prefer):
                    return o

            # Шкала владения / прочее: выбираем по стратегии среди «нормальных» вариантов
            candidates = [o for o, nz in zip(opts, norms)
                          if not any(c in nz for c in CUSTOM_OPTIONS)
                          and not any(neg in nz for neg in NEGATIVE_OPTIONS)]
            if not candidates:
                candidates = [o for o, nz in zip(opts, norms) if not any(c in nz for c in CUSTOM_OPTIONS)]
            if not candidates:
                candidates = opts
            if not candidates:
                return ""

            strat = self.kb["fallbacks"].get("skill_level", "last")
            if strat == "first":
                return candidates[0]
            if strat == "middle":
                return candidates[len(candidates) // 2]
            return candidates[-1]  # last / максимум

        return ""

    # ---------- Заполнение ----------
    def _dismiss_overlays(self, page):
        """Убирает фиксированные оверлеи (cookie-плашка, виджет чатов), которые
        перекрывают варианты снизу экрана и воруют клики."""
        selectors = [
            "[data-qa='cookie-policy-informer-accept']",
            "[data-qa='cookies-policy-informer-accept-button']",
            "button:has-text('Понятно')",
            "[data-qa='chatik-close-chatik']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.click(force=True)
                    page.wait_for_timeout(150)
            except Exception:
                pass

    def fill(self, page, questions=None, dry_run=False):
        """Заполняет ответы. Возвращает список результатов. НЕ нажимает отправку."""
        self._dismiss_overlays(page)
        if questions is None:
            questions = self.parse(page)
        bodies = page.locator("[data-qa='task-body']")
        results = []
        for q in questions:
            ans = self.decide(q)
            filled = False
            reason = ""
            body = bodies.nth(q["index"])
            try:
                if q["type"] == "textarea":
                    # текстовое поле НИКОГДА не оставляем пустым
                    if not ans:
                        ans = self.kb["fallbacks"].get("open_text") or "Готов обсудить детали на собеседовании."
                    area = body.locator("textarea").first
                    area.fill(ans)
                    filled = True
                elif q["type"] in ("radio", "checkbox"):
                    target = _norm(ans)
                    cells = body.locator("label[data-qa='cell']")
                    cn = cells.count()
                    texts = []
                    for c in range(cn):
                        try:
                            texts.append(_norm(cells.nth(c).text_content() or ""))
                        except Exception:
                            texts.append("")
                    chosen = None
                    for c in range(cn):
                        if target and (texts[c] == target or target in texts[c]):
                            chosen = c
                            break
                    if chosen is None and cn > 0:
                        # ловец: выбираем безопасный фолбэк, чтобы вопрос не остался без ответа
                        chosen = self._fallback_index(texts)
                        reason = f"вариант '{ans}' не найден -> фолбэк #{chosen}"
                    if chosen is not None and cn > 0:
                        filled = self._select_cell(page, cells.nth(chosen))
                        if not filled:
                            reason = (reason + "; " if reason else "") + "клик не зафиксировал выбор"
                    else:
                        reason = "нет вариантов для выбора"
                else:
                    reason = "неизвестный тип"
            except Exception as e:
                reason = str(e)
            results.append({"index": q["index"], "question": q["question"],
                            "type": q["type"], "answer": ans, "filled": filled, "reason": reason})
        return results

    def _fallback_index(self, texts):
        """Безопасный вариант, если ответ не распознан: последний не-кастомный и
        не-негативный; иначе последний не-кастомный; иначе последний; иначе 0."""
        def is_custom(t):
            return any(c in t for c in CUSTOM_OPTIONS)

        def is_negative(t):
            return any(n in t for n in NEGATIVE_OPTIONS)

        # приоритет — утвердительный вариант ("Да"), правило «всегда Да»
        prefer = _norm(self.kb["fallbacks"].get("yesno_prefer", "да"))
        for i, t in enumerate(texts):
            if t == prefer or (prefer and t.startswith(prefer + " ")):
                return i

        idxs = list(range(len(texts)))
        good = [i for i in idxs if not is_custom(texts[i]) and not is_negative(texts[i])]
        if good:
            return good[-1]
        noncustom = [i for i in idxs if not is_custom(texts[i])]
        if noncustom:
            return noncustom[-1]
        return idxs[-1] if idxs else 0

    def _select_cell(self, page, cell):
        """Кликает по варианту и проверяет, что выбор зафиксировался (важно из-за
        ре-рендеров React при быстрых кликах). До 3 попыток. True, если input отмечен."""
        try:
            inp = cell.locator("input").first
        except Exception:
            inp = None
        for attempt in range(3):
            try:
                cell.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                pass
            try:
                # attempt 0: обычный клик; далее — JS-клик (игнорирует перекрытие оверлеями)
                if attempt == 0:
                    cell.click(force=True)
                else:
                    cell.evaluate("el => el.click()")
            except Exception:
                pass
            try:
                page.wait_for_timeout(200)
            except Exception:
                pass
            # Проверка фиксации выбора по реальному input
            try:
                if inp is not None and inp.is_checked():
                    return True
            except Exception:
                return True
        return False

    def all_answered(self, results):
        """True, если все вопросы удалось заполнить."""
        return bool(results) and all(r["filled"] for r in results)
