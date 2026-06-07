from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ctypes
import queue
import shutil
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait


APP_TITLE = "Selenium Window Runner"
LINK_FILE = Path("link.txt")
MAX_LINKS = 4


class RunnerConfig:
    def __init__(
        self,
        browser,
        links,
        loop_count,
        wait_after_open,
        wait_after_scroll,
        wait_before_close_all,
        wait_between_rounds,
        scroll_pixels,
        page_load_timeout,
        retry_per_round,
    ):
        self.browser = browser
        self.links = links
        self.loop_count = loop_count
        self.wait_after_open = wait_after_open
        self.wait_after_scroll = wait_after_scroll
        self.wait_before_close_all = wait_before_close_all
        self.wait_between_rounds = wait_between_rounds
        self.scroll_pixels = scroll_pixels
        self.page_load_timeout = page_load_timeout
        self.retry_per_round = retry_per_round


class SeleniumRunner:
    def __init__(self, config, log, stop_event):
        self.config = config
        self.log = log
        self.stop_event = stop_event

    def run(self):
        count = len(self.config.links)
        mode_label = "1 cua so" if count == 1 else f"{count} cua so"

        for index in range(1, self.config.loop_count + 1):
            if self.stop_event.is_set():
                self.log("Da dung theo yeu cau")
                break

            round_started_at = time.perf_counter()
            self.log(f"Lan lap {index}/{self.config.loop_count} - {mode_label}")

            if count == 1:
                ok = self.run_one_round_with_retry(self.config.links[0])
            else:
                ok = self.run_one_round_multi_with_retry(self.config.links)

            if not ok:
                self.log("Khong the mo trang bang Selenium, dung chuong trinh")
                break

            round_elapsed = time.perf_counter() - round_started_at
            self.log(f"Thoi gian vong {index}: {round_elapsed:.2f} giay")

            if index < self.config.loop_count and self.config.wait_between_rounds > 0:
                self.sleep_with_stop(self.config.wait_between_rounds)
                total_elapsed = time.perf_counter() - round_started_at
                self.log(f"Tong thoi gian vong {index} gom ca nghi: {total_elapsed:.2f} giay")

        self.log("Hoan tat")

    def run_one_round_with_retry(self, url):
        for attempt in range(1, self.config.retry_per_round + 1):
            try:
                self.run_one_round(url)
                return True
            except (TimeoutException, WebDriverException) as error:
                self.log(f"Loi Selenium lan thu {attempt}/{self.config.retry_per_round}: {error.msg}")
                self.sleep_with_stop(2)

        return False

    def run_one_round_multi_with_retry(self, urls):
        for attempt in range(1, self.config.retry_per_round + 1):
            try:
                return self.run_one_round_multi(urls)
            except (TimeoutException, WebDriverException) as error:
                self.log(f"Loi Selenium lan thu {attempt}/{self.config.retry_per_round}: {error.msg}")
                self.sleep_with_stop(2)

        return False

    def create_driver(self):
        user_data_dir = tempfile.mkdtemp(prefix="selenium-profile-")

        if self.config.browser == "edge":
            options = EdgeOptions()
            self.add_common_browser_options(options, user_data_dir)
            service = EdgeService(log_output=None)
            driver = webdriver.Edge(options=options, service=service)
        else:
            options = ChromeOptions()
            self.add_common_browser_options(options, user_data_dir)
            driver = webdriver.Chrome(options=options)

        driver._temporary_user_data_dir = user_data_dir
        driver.set_page_load_timeout(self.config.page_load_timeout)
        return driver

    def add_common_browser_options(self, options, user_data_dir):
        options.page_load_strategy = "eager"
        options.add_argument("--start-maximized")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-background-networking")
        options.add_argument(f"--user-data-dir={user_data_dir}")

    def close_driver(self, driver):
        user_data_dir = getattr(driver, "_temporary_user_data_dir", None)

        try:
            driver.quit()
        except WebDriverException:
            pass

        if user_data_dir:
            shutil.rmtree(user_data_dir, ignore_errors=True)

    def close_drivers_concurrently(self, drivers):
        if not drivers:
            return

        with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
            futures = [executor.submit(self.close_driver, driver) for driver in drivers]

            for future in futures:
                future.result()

    def run_one_round(self, url):
        driver = self.create_driver()

        try:
            driver.get(url)
            self.wait_until_page_ready(driver)
            self.log(f"Da mo link bang Selenium: {url}")

            self.sleep_with_stop(self.config.wait_after_open)
            self.move_mouse_to_page_percent(driver)
            self.scroll_page(driver)
            self.sleep_with_stop(self.config.wait_after_scroll)
        finally:
            self.close_driver(driver)

    def run_one_round_multi(self, urls):
        drivers = []

        try:
            total_count = len(urls)

            for idx, url in enumerate(urls):
                if self.stop_event.is_set():
                    return True

                driver = self.create_driver()
                drivers.append(driver)
                self.set_driver_grid_position(driver, idx, total_count)

                driver.get(url)
                self.wait_until_page_ready(driver)
                self.log(f"Da mo link {idx + 1} bang Selenium: {url}")

            self.set_driver_grid(drivers)
            self.sleep_with_stop(self.config.wait_after_open)

            for driver in drivers:
                if self.stop_event.is_set():
                    break

                self.move_mouse_to_page_percent(driver)
                self.scroll_page(driver)
                self.sleep_with_stop(self.config.wait_after_scroll)

            self.sleep_with_stop(self.config.wait_before_close_all)
            return True
        finally:
            self.close_drivers_concurrently(drivers)

    def wait_until_page_ready(self, driver):
        WebDriverWait(driver, self.config.page_load_timeout).until(
            lambda active_driver: active_driver.execute_script("return document.readyState")
            in ("interactive", "complete")
        )

    def move_mouse_to_page_percent(self, driver):
        size = driver.get_window_size()
        x = int(size["width"] * 0.5)
        y = int(size["height"] * 0.5)

        ActionChains(driver).move_by_offset(x, y).perform()
        ActionChains(driver).move_by_offset(-x, -y).perform()

    def scroll_page(self, driver):
        driver.execute_script("window.scrollBy(0, arguments[0]);", int(self.config.scroll_pixels))

    def set_driver_grid(self, drivers):
        for idx, driver in enumerate(drivers[:MAX_LINKS]):
            self.set_driver_grid_position(driver, idx, len(drivers))

    def set_driver_grid_position(self, driver, index, total_count):
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)

        if total_count == 2:
            half_width = max(1, screen_width // 2)
            if index == 0:
                driver.set_window_position(0, 0)
                driver.set_window_size(half_width, screen_height)
            else:
                driver.set_window_position(half_width, 0)
                driver.set_window_size(screen_width - half_width, screen_height)
            return

        cell_width = max(1, screen_width // 2)
        cell_height = max(1, screen_height // 2)
        positions = [
            (0, 0),
            (cell_width, 0),
            (0, cell_height),
            (cell_width, cell_height),
        ]
        x, y = positions[index]
        driver.set_window_position(x, y)
        driver.set_window_size(cell_width, cell_height)

    def sleep_with_stop(self, seconds):
        end_time = time.time() + max(0, float(seconds))

        while time.time() < end_time:
            if self.stop_event.is_set():
                return
            time.sleep(min(0.2, end_time - time.time()))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("920x680")
        self.minsize(820, 620)

        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None

        self.browser_var = tk.StringVar(value="edge")
        self.loop_count_var = tk.StringVar(value="1000")
        self.wait_after_open_var = tk.StringVar(value="0")
        self.wait_after_scroll_var = tk.StringVar(value="0")
        self.wait_before_close_all_var = tk.StringVar(value="3")
        self.wait_between_rounds_var = tk.StringVar(value="0")
        self.scroll_pixels_var = tk.StringVar(value="2500")
        self.page_load_timeout_var = tk.StringVar(value="15")
        self.retry_per_round_var = tk.StringVar(value="2")

        self.build_ui()
        self.load_links_from_file()
        self.after(100, self.flush_log_queue)

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.LabelFrame(root, text="Cau hinh")
        config_frame.pack(fill=tk.X)

        ttk.Label(config_frame, text="Browser").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        browser_box = ttk.Combobox(
            config_frame,
            textvariable=self.browser_var,
            values=("edge", "chrome"),
            width=12,
            state="readonly",
        )
        browser_box.grid(row=0, column=1, sticky=tk.W, padx=8, pady=6)

        self.add_entry(config_frame, "So vong", self.loop_count_var, 0, 2)
        self.add_entry(config_frame, "Cho sau mo", self.wait_after_open_var, 0, 4)
        self.add_entry(config_frame, "Cho sau cuon", self.wait_after_scroll_var, 1, 0)
        self.add_entry(config_frame, "Cho truoc dong", self.wait_before_close_all_var, 1, 2)
        self.add_entry(config_frame, "Nghi giua vong", self.wait_between_rounds_var, 1, 4)
        self.add_entry(config_frame, "Pixel cuon", self.scroll_pixels_var, 2, 0)
        self.add_entry(config_frame, "Timeout load", self.page_load_timeout_var, 2, 2)
        self.add_entry(config_frame, "Retry", self.retry_per_round_var, 2, 4)

        for col in range(6):
            config_frame.columnconfigure(col, weight=1)

        links_frame = ttk.LabelFrame(root, text=f"Links, toi da {MAX_LINKS} dong")
        links_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.links_text = tk.Text(links_frame, height=8, wrap=tk.NONE)
        self.links_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_runner)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_runner, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=8)

        ttk.Button(button_frame, text="Save links", command=self.save_links_to_file).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear log", command=self.clear_log).pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(root, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def add_entry(self, parent, label, variable, row, column):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky=tk.W, padx=8, pady=6)
        entry = ttk.Entry(parent, textvariable=variable, width=12)
        entry.grid(row=row, column=column + 1, sticky=tk.W, padx=8, pady=6)

    def load_links_from_file(self):
        if not LINK_FILE.exists():
            return

        self.links_text.delete("1.0", tk.END)
        self.links_text.insert("1.0", LINK_FILE.read_text(encoding="utf-8").strip())

    def save_links_to_file(self):
        links = self.get_links()
        LINK_FILE.write_text("\n".join(links), encoding="utf-8")
        self.log(f"Da luu {len(links)} link vao link.txt")

    def get_links(self):
        raw_lines = self.links_text.get("1.0", tk.END).splitlines()
        links = [line.strip() for line in raw_lines if line.strip()]
        return links[:MAX_LINKS]

    def get_config(self):
        links = self.get_links()

        if not links:
            raise ValueError("Chua co link")

        return RunnerConfig(
            browser=self.browser_var.get().strip().lower(),
            links=links,
            loop_count=self.parse_int(self.loop_count_var.get(), "So vong", minimum=1, maximum=1000),
            wait_after_open=self.parse_float(self.wait_after_open_var.get(), "Cho sau mo", minimum=0),
            wait_after_scroll=self.parse_float(self.wait_after_scroll_var.get(), "Cho sau cuon", minimum=0),
            wait_before_close_all=self.parse_float(self.wait_before_close_all_var.get(), "Cho truoc dong", minimum=0),
            wait_between_rounds=self.parse_float(self.wait_between_rounds_var.get(), "Nghi giua vong", minimum=0),
            scroll_pixels=self.parse_int(self.scroll_pixels_var.get(), "Pixel cuon", minimum=-20000, maximum=20000),
            page_load_timeout=self.parse_int(self.page_load_timeout_var.get(), "Timeout load", minimum=1, maximum=120),
            retry_per_round=self.parse_int(self.retry_per_round_var.get(), "Retry", minimum=1, maximum=5),
        )

    def parse_int(self, value, label, minimum=None, maximum=None):
        try:
            number = int(value)
        except ValueError as error:
            raise ValueError(f"{label} phai la so nguyen") from error

        if minimum is not None and number < minimum:
            raise ValueError(f"{label} phai >= {minimum}")
        if maximum is not None and number > maximum:
            raise ValueError(f"{label} phai <= {maximum}")
        return number

    def parse_float(self, value, label, minimum=None, maximum=None):
        try:
            number = float(value)
        except ValueError as error:
            raise ValueError(f"{label} phai la so") from error

        if minimum is not None and number < minimum:
            raise ValueError(f"{label} phai >= {minimum}")
        if maximum is not None and number > maximum:
            raise ValueError(f"{label} phai <= {maximum}")
        return number

    def start_runner(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        try:
            config = self.get_config()
        except ValueError as error:
            messagebox.showerror(APP_TITLE, str(error))
            return

        self.stop_event.clear()
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.log("Bat dau chay")

        runner = SeleniumRunner(config, self.log, self.stop_event)
        self.worker_thread = threading.Thread(target=self.run_worker, args=(runner,), daemon=True)
        self.worker_thread.start()

    def run_worker(self, runner):
        try:
            runner.run()
        except Exception as error:
            self.log(f"Loi: {error}")
        finally:
            self.log_queue.put(("__done__", None))

    def stop_runner(self):
        self.stop_event.set()
        self.log("Dang dung...")

    def flush_log_queue(self):
        try:
            while True:
                item, value = self.log_queue.get_nowait()

                if item == "__log__":
                    self.write_log(value)
                elif item == "__done__":
                    self.start_button.configure(state=tk.NORMAL)
                    self.stop_button.configure(state=tk.DISABLED)
        except queue.Empty:
            pass

        self.after(100, self.flush_log_queue)

    def log(self, message):
        self.log_queue.put(("__log__", message))

    def write_log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


if __name__ == "__main__":
    App().mainloop()
