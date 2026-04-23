import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

ARTIFACTS_DIR = Path("ui_test_artifacts")


@pytest.fixture(scope="session")
def ui_base_url():
    return os.getenv("UI_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture
def driver():
    options = Options()
    # Keep local debugging friendly: visible browser by default.
    if os.getenv("UI_HEADLESS", "0") == "1":
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1280,900")
    if os.getenv("UI_DISABLE_GPU", "1") == "1":
        options.add_argument("--disable-gpu")
    if os.getenv("UI_NO_SANDBOX", "0") == "1":
        # Useful in some CI containers; off by default for local dev.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    yield browser
    browser.quit()


@pytest.fixture
def wait(driver):
    # Centralized explicit wait for stable UI tests.
    return WebDriverWait(driver, 10)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    driver = item.funcargs.get("driver")
    if not driver:
        return

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = item.nodeid.replace("/", "_").replace("::", "__")

    screenshot_path = ARTIFACTS_DIR / f"{safe_name}_{timestamp}.png"
    html_path = ARTIFACTS_DIR / f"{safe_name}_{timestamp}.html"

    driver.save_screenshot(str(screenshot_path))
    html_path.write_text(driver.page_source, encoding="utf-8")

    print(f"\n[ui-artifact] screenshot: {screenshot_path}")
    print(f"[ui-artifact] html: {html_path}")
    print(f"[ui-artifact] url: {driver.current_url}")
