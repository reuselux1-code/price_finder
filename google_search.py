from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils import dedupe_urls, polite_delay


@dataclass
class GoogleSearchConfig:
    max_results: int = 20
    min_delay: float = 1.2
    max_delay: float = 2.8
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    language: str = "fr"


def _build_driver(config: GoogleSearchConfig) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={config.user_agent}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def search_google(query: str, config: GoogleSearchConfig) -> List[str]:
    driver = _build_driver(config)
    urls: List[str] = []
    try:
        params = f"?hl={config.language}"
        driver.get(f"https://www.google.com/{params}")
        polite_delay(config.min_delay, config.max_delay)
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()
        polite_delay(config.min_delay, config.max_delay)

        link_elements = driver.find_elements(By.CSS_SELECTOR, "div#search a")
        for element in link_elements:
            href = element.get_attribute("href")
            if not href:
                continue
            if not href.startswith("http"):
                continue
            if "google.com/aclk" in href or "googleadservices" in href:
                continue
            urls.append(href)
            if len(urls) >= config.max_results:
                break
    except Exception:
        logging.exception("Google search failed")
    finally:
        driver.quit()

    return dedupe_urls(urls)
