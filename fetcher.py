from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclass
class FetchConfig:
    timeout: int = 12
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


def _selenium_driver(user_agent: str) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def fetch_content(url: str, config: FetchConfig) -> Optional[str]:
    headers = {"User-Agent": config.user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=config.timeout)
        if response.status_code == 200 and response.text:
            return response.text
    except requests.RequestException:
        logging.info("Requests failed for %s, falling back to Selenium", url)

    try:
        driver = _selenium_driver(config.user_agent)
        try:
            driver.get(url)
            return driver.page_source
        finally:
            driver.quit()
    except Exception:
        logging.exception("Selenium fetch failed for %s", url)
        return None
