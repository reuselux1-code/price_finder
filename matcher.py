from __future__ import annotations

import re


def normalize_reference(text: str) -> str:
    cleaned = re.sub(r"[\s\-_'\"]", "", text)
    return cleaned.upper()


def page_contains_reference(page_text: str, reference: str) -> bool:
    normalized_ref = normalize_reference(reference)
    normalized_page = normalize_reference(page_text)
    return normalized_ref in normalized_page
