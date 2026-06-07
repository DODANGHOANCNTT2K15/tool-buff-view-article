from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import ctypes
import os
import shutil
import sys
import tempfile
import time

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait


LINK_FILE = Path("link.txt")

BROWSER = "edge"  # edge or chrome
LOOP_COUNT = 1000
WAIT_AFTER_OPEN_SECONDS = 0
WAIT_AFTER_SCROLL_SECONDS = 0
WAIT_BEFORE_CLOSE_ALL_SECONDS = 3
WAIT_BETWEEN_ROUNDS_SECONDS = 0
SCROLL_PIXELS = 2500
MOUSE_X_PERCENT = 0.5
MOUSE_Y_PERCENT = 0.5
PAGE_LOAD_TIMEOUT_SECONDS = 10
RETRY_PER_ROUND = 2
SELENIUM_PROXY_SERVER = os.getenv("SELENIUM_PROXY_SERVER", "").strip()


def read_link():
    text = LINK_FILE.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def read_links():
    if not LINK_FILE.exists():
        return []

    lines = [line.strip() for line in LINK_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[:4]


def add_common_browser_options(options, user_data_dir):
    options.page_load_strategy = "eager"
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-background-networking")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    if SELENIUM_PROXY_SERVER:
        options.add_argument(f"--proxy-server={SELENIUM_PROXY_SERVER}")

    return options


def create_driver():
    user_data_dir = tempfile.mkdtemp(prefix="selenium-profile-")

    if BROWSER.lower() == "edge":
        options = EdgeOptions()
        add_common_browser_options(options, user_data_dir)
        service = EdgeService(log_output=None)
        driver = webdriver.Edge(options=options, service=service)
        driver._temporary_user_data_dir = user_data_dir
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        return driver

    options = ChromeOptions()
    add_common_browser_options(options, user_data_dir)
    driver = webdriver.Chrome(options=options)
    driver._temporary_user_data_dir = user_data_dir
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver


def close_driver(driver):
    user_data_dir = getattr(driver, "_temporary_user_data_dir", None)

    try:
        driver.quit()
    except WebDriverException:
        pass

    if user_data_dir:
        shutil.rmtree(user_data_dir, ignore_errors=True)


def close_drivers_concurrently(drivers):
    if not drivers:
        return

    with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
        futures = [executor.submit(close_driver, driver) for driver in drivers]

        for future in futures:
            future.result()


def set_driver_grid(drivers):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    count = len(drivers)

    if count == 2:
        half_width = max(1, screen_width // 2)
        drivers[0].set_window_position(0, 0)
        drivers[0].set_window_size(half_width, screen_height)
        drivers[1].set_window_position(half_width, 0)
        drivers[1].set_window_size(screen_width - half_width, screen_height)
        return

    cell_width = max(1, screen_width // 2)
    cell_height = max(1, screen_height // 2)

    positions = [
        (0, 0),
        (cell_width, 0),
        (0, cell_height),
        (cell_width, cell_height),
    ]

    for idx, driver in enumerate(drivers[:4]):
        x, y = positions[idx]
        driver.set_window_position(x, y)
        driver.set_window_size(cell_width, cell_height)


def set_driver_grid_position(driver, index, total_count):
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


def wait_until_page_ready(driver):
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT_SECONDS).until(
        lambda active_driver: active_driver.execute_script(
            "return document.readyState"
        )
        in ("interactive", "complete")
    )


def move_mouse_to_page_percent(driver, x_percent=MOUSE_X_PERCENT, y_percent=MOUSE_Y_PERCENT):
    size = driver.get_window_size()
    x = int(size["width"] * x_percent)
    y = int(size["height"] * y_percent)

    ActionChains(driver).move_by_offset(x, y).perform()
    ActionChains(driver).move_by_offset(-x, -y).perform()


def scroll_page(driver, pixels=SCROLL_PIXELS):
    driver.execute_script("window.scrollBy(0, arguments[0]);", int(pixels))


def run_one_round(url):
    driver = create_driver()

    try:
        driver.get(url)
        wait_until_page_ready(driver)
        print(f"Da mo link bang Selenium: {url}")

        time.sleep(WAIT_AFTER_OPEN_SECONDS)
        move_mouse_to_page_percent(driver)
        scroll_page(driver)
        time.sleep(WAIT_AFTER_SCROLL_SECONDS)
    finally:
        close_driver(driver)


def run_one_round_multi(urls):
    drivers = []

    try:
        total_count = len(urls)

        for idx, url in enumerate(urls):
            driver = create_driver()
            drivers.append(driver)
            set_driver_grid_position(driver, idx, total_count)

            driver.get(url)
            wait_until_page_ready(driver)
            print(f"Da mo link {idx + 1} bang Selenium: {url}")

        set_driver_grid(drivers)

        time.sleep(WAIT_AFTER_OPEN_SECONDS)

        for driver in drivers:
            move_mouse_to_page_percent(driver)
            scroll_page(driver)
            time.sleep(WAIT_AFTER_SCROLL_SECONDS)

        time.sleep(WAIT_BEFORE_CLOSE_ALL_SECONDS)
        return True
    finally:
        close_drivers_concurrently(drivers)


def run_one_round_multi_with_retry(urls):
    for attempt in range(1, RETRY_PER_ROUND + 1):
        try:
            return run_one_round_multi(urls)
        except (TimeoutException, WebDriverException) as error:
            print(f"Loi Selenium lan thu {attempt}/{RETRY_PER_ROUND}: {error.msg}")
            time.sleep(2)
    return False


def run_one_round_with_retry(url):
    for attempt in range(1, RETRY_PER_ROUND + 1):
        try:
            run_one_round(url)
            return True
        except (TimeoutException, WebDriverException) as error:
            print(f"Loi Selenium lan thu {attempt}/{RETRY_PER_ROUND}: {error.msg}")
            time.sleep(2)

    return False


def main():
    links = read_links()

    if not links:
        print("link.txt dang trong")
        return

    if SELENIUM_PROXY_SERVER:
        print(f"Dang dung proxy Selenium: {SELENIUM_PROXY_SERVER}")

    count = len(links)
    if count > 4:
        print("Link file co hon 4 dong; chi su dung 4 dong dau tien")
        links = links[:4]
        count = 4

    if count == 1:
        mode_label = "1 cua so"
    else:
        mode_label = f"{count} cua so"

    for index in range(1, LOOP_COUNT + 1):
        round_started_at = time.perf_counter()
        print(f"Lan lap {index}/{LOOP_COUNT} - {mode_label}")

        if count == 1:
            if not run_one_round_with_retry(links[0]):
                print("Khong the mo trang bang Selenium, dung chuong trinh")
                break
        else:
            if not run_one_round_multi_with_retry(links):
                print(f"Khong the mo {count} trang bang Selenium, dung chuong trinh")
                break

        round_elapsed = time.perf_counter() - round_started_at
        print(f"Thoi gian vong {index}: {round_elapsed:.2f} giay")

        if index < LOOP_COUNT:
            time.sleep(WAIT_BETWEEN_ROUNDS_SECONDS)
            total_elapsed = time.perf_counter() - round_started_at
            print(f"Tong thoi gian vong {index} gom ca nghi: {total_elapsed:.2f} giay")


if __name__ == "__main__":
    main()
