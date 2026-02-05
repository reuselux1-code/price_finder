from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Iterable, List, Optional
from urllib.parse import urlparse


LOG_FILE = "app.log"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def polite_delay(min_s: float = 1.2, max_s: float = 2.8) -> None:
    time.sleep(random.uniform(min_s, max_s))


def dedupe_urls(urls: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        output.append(url)
    return output


def dedupe_by_domain(urls: Iterable[str]) -> List[str]:
    seen_domains = set()
    output = []
    for url in urls:
        domain = urlparse(url).netloc.lower()
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        output.append(url)
    return output


def save_json(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except OSError:
        logging.exception("Failed to save JSON output")


def safe_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        return None
