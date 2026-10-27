# Вариант 4 авиасальса
# Пирамидковые импорты потому что египетская сила
import re
import time
import pandas as pd
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime, date, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# главное капчу в начале быстро натыкать и будет нормально
class Parser:
    # Ещё пришлось думать как заставить это работать без мучений с календарём
    ORIGIN = "MSQ"
    DEST = "SYX"
    PASSENGERS = "1"
    # Штуки которые будут логироваться
    LOGGED_METHODS = ("accept_cookies", "go_to_search_page", "tickets_available",
        "parse_page", "run",)
    # При мне работало с божьей помощью
    def __init__(self, link):
        self.link = link
        self.tickets_list = []
        self.func_logs = []
        self._wrap_logged_methods()
        options = self.proxy()
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.link)
        self.accept_cookies()
    # Прокся
    def proxy(self):
        with open(r"C:\Users\JustAtsu\Desktop\lab\aviasalsa\proxy_list.txt", 'r') as proxlist:
            proxy_list = proxlist.read()
        proxy_list1 = proxy_list.split('\n')
        proxy = proxy_list1[randint(0, len(proxy_list1) - 1)]
        self.profile = FirefoxProfile()
        profile = self.profile
        profile.set_preference("general.useragent.override",
            "Godzilla/5.0 (Linux Ubuntu 22.04 LTS; x64; rv:22.04) "
            "Gecko/20100101 Firebox/121.0")
        ip, port = proxy.split(':')
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.http", f"{ip}")
        profile.set_preference("network.proxy.http_port", int(port))
        profile.set_preference("network.proxy.ssl", f"{ip}")
        profile.set_preference("network.proxy.ssl_port", int(port))
        profile.set_preference("network.proxy.no_proxies_on",
                                "localhost, 127.0.0.1")
        options = FirefoxOptions()
        options.profile = profile
        print(ip, port)
        return options
    # Да да логи угу
    def _log_call(self, func_name, start_dt, result=None, error=None):
        if error is not None:
            res = f"Ошибка: {error}"
        elif isinstance(result, list):
            res = f"{len(result)} шт."
        elif result is None:
            res = "выполнено"
        else:
            res = str(result)
        self.func_logs.append(
            [func_name, start_dt.strftime("%Y-%m-%d %H:%M:%S"), res])
    def _wrap_logged_methods(self):
        for name in self.LOGGED_METHODS:
            original = getattr(type(self), name, None)
            if original is None:
                continue
            def make_wrapper(func, fname):
                def wrapper(*args, **kwargs):
                    start = datetime.now()
                    try:
                        result = func(self, *args, **kwargs)
                        self._log_call(fname, start, result=result)
                        return result
                    except Exception as e:
                        self._log_call(fname, start, error=e)
                        raise
                return wrapper
            setattr(self, name, make_wrapper(original, name))
    # Оно что-то тыкает, пусть тыкает
    def _js_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            element)
    # Печенюшковые страдания и буллинг отелей
    def accept_cookies(self, timeout=10):
        try:
            button = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-test-id="accept-cookies-button"]')))
            self._js_click(button)
            try:
                checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                '[data-test-id="hotels-checkbox"] input[type="checkbox"]')))
                if checkbox.is_selected():
                    label = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="hotels-checkbox"]')
                    self._js_click(label)
            # Если нет кнопок то и не надо ну и пожалуйста
            except Exception:
                    pass
        except Exception:
            pass
    def build_search_url(self, date_str):
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        code = f"{d.day:02d}{d.month:02d}"
        return (f"https://www.aviasales.by/search/"
                f"{self.ORIGIN}{code}{self.DEST}{self.PASSENGERS}")
    def go_to_search_page(self, date_str):
        url = self.build_search_url(date_str)
        self.driver.get(url)
        time.sleep(5)
    # Наличие билетов и прочие страдания
    def tickets_available(self, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            previews = self.driver.find_elements(
                By.CSS_SELECTOR, '[data-test-id="ticket-preview"]')
            if previews:
                return True
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            if re.search(r"(не найдено|нет билет|отсутству|не удалось найти)",
                        body_text, re.IGNORECASE):
                return False
            time.sleep(1)
        return False
    # Ало билеты дада дорого
    @staticmethod
    def _clean(text):
        return re.sub(r"\s+", " ",
                    text.replace("\u00a0", " ").replace("\u202f", " ")).strip()
    BADGE_LABELS = {
        "ticket-preview-badge-cheapest": "Самый дешёвый",
        "ticket-preview-badge-fastest": "Самый быстрый",
        "ticket-preview-badge-cheapest_convenient":
            "Самый дешёвый с удобной пересадкой",}
    def parse_ticket(self, ticket):
        badge = ticket.find_element(
            By.CSS_SELECTOR,
            '[data-test-id="ticket-preview-badge-cheapest"], '
            '[data-test-id="ticket-preview-badge-fastest"], '
            '[data-test-id="ticket-preview-badge-cheapest_convenient"]')
        badge_id = badge.get_attribute("data-test-id")
        label = self.BADGE_LABELS.get(badge_id, badge_id)
        price_el = ticket.find_element(By.CSS_SELECTOR, '[data-test-id="price"]')
        price = self._clean(price_el.text)
        time_blocks = ticket.find_elements(By.CSS_SELECTOR, ".s__TPEe2f9fw2sce6Si")
        dep_time = arr_time = ""
        dep_city = arr_city = ""
        dep_date = arr_date = ""
        if len(time_blocks) >= 2:
            results = {}
            for key, block in (("dep", time_blocks[0]), ("arr", time_blocks[-1])):
                texts = [
                    self._clean(t.text)
                    for t in block.find_elements(
                        By.CSS_SELECTOR, '[data-test-id="text"]')]
                if len(texts) >= 3:
                    results[key] = (texts[0], texts[1], texts[2])
                else:
                    time_ = next(
                        (t for t in texts if re.match(r"^\d{1,2}:\d{2}$", t)), "")
                    date_ = next((t for t in texts if "," in t), "")
                    city_ = next(
                        (t for t in texts if t not in (time_, date_)), "")
                    results[key] = (time_, city_, date_)
            dep_time, dep_city, dep_date = results["dep"]
            arr_time, arr_city, arr_date = results["arr"]
        # Запятые в датах убивают
        dep_date = re.sub(r",\s*", " ", dep_date)
        arr_date = re.sub(r",\s*", " ", arr_date)
        line = (f"{label},{price}, {dep_date}, {dep_time}, {dep_city}, "
                f"{arr_date}, {arr_time}, {arr_city}")
        self.tickets_list.append(line)
        return line
    def parse_page(self):
        time.sleep(3)
        badges = self.driver.find_elements(
            By.CSS_SELECTOR,
            '[data-test-id="ticket-preview-badge-cheapest"], '
            '[data-test-id="ticket-preview-badge-fastest"], '
            '[data-test-id="ticket-preview-badge-cheapest_convenient"]')
        for badge in badges:
            try:
                ticket = badge.find_element(
                    By.XPATH, './ancestor::div[@data-test-id="ticket-preview"]')
                self.parse_ticket(ticket)
            except Exception as e:
                print(f"Не удалось распарсить билет: {e}")
        return self.tickets_list
    def parse_all_days(self):
        today = datetime.now().date()
        end_of_year = date(today.year, 12, 31)
        current = today
        while current <= end_of_year:
            date_str = current.strftime("%Y-%m-%d")
            self.go_to_search_page(date_str)
            try:
                if self.tickets_available():
                    self.parse_page()
                else:
                    print(f"[{date_str}] Билетов нет")
            except Exception as e:
                print(f"Ошибка на дате {date_str}: {e}")
            current += timedelta(days=1)
        return self.tickets_list
    def run(self):
        return self.parse_all_days()
    # Ого это что csv
    def save_tickets(self, filename="tickets.csv"):
        if not self.tickets_list:
            print("Нет билетов для сохранения")
            return
        rows = [[p.strip() for p in line.split(",")] for line in self.tickets_list]
        max_len = max(len(r) for r in rows)
        rows = [r + [""] * (max_len - len(r)) for r in rows]
        columns = [
            "Тип", "Цена", "Дата вылета", "Время вылета", "Город вылета",
            "Дата прилёта", "Время прилёта", "Город прилёта",
        ][:max_len]
        df = pd.DataFrame(rows, columns=columns)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Билеты сохранены в {filename} ({len(df)} шт.)")
    def save_function_logs(self, filename="function_logs.csv"):
        logs = getattr(self, "func_logs", [])
        df = pd.DataFrame(logs, columns=["Функция", "Время запуска", "Результат"])
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Логи в {filename} ({len(df)} записей)")
    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass
    # Он смешнявый
    def __del__(self):
        print('ъъъъъ')
