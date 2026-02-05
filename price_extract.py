from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from utils import safe_float


SHIPPING_KEYWORDS = {
    "shipping",
    "livraison",
    "postage",
    "shipping cost",
    "frais de port",
}

CURRENCY_MAP = {
    "€": "EUR",
    "eur": "EUR",
    "$": "USD",
    "usd": "USD",
    "£": "GBP",
    "gbp": "GBP",
}

PRICE_PATTERN = re.compile(
    r"(?P<prefix>€|\$|£|EUR|USD|GBP)?\s*"
    r"(?P<amount>\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})|\d+(?:[\.,]\d{2})?)"
    r"\s*(?P<suffix>€|\$|£|EUR|USD|GBP)?",
    re.IGNORECASE,
)


@dataclass
class PriceCandidate:
    amount: float
    currency: str


def _normalize_amount(amount_raw: str) -> Optional[float]:
    cleaned = amount_raw.replace(" ", "")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "")
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    return safe_float(cleaned)


def _has_shipping_context(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 40) : min(len(text), end + 40)].lower()
    return any(keyword in window for keyword in SHIPPING_KEYWORDS)


def extract_single_price(text: str) -> Optional[PriceCandidate]:
    candidates: List[PriceCandidate] = []
    lowered = text.lower()
    for match in PRICE_PATTERN.finditer(text):
        start, end = match.span()
        if _has_shipping_context(lowered, start, end):
            continue
        amount = _normalize_amount(match.group("amount"))
        if amount is None:
            continue
        prefix = (match.group("prefix") or "").lower()
        suffix = (match.group("suffix") or "").lower()
        currency_token = prefix or suffix
        currency = CURRENCY_MAP.get(currency_token, "")
        if not currency:
            continue
        candidates.append(PriceCandidate(amount=amount, currency=currency))

    if not candidates:
        return None

    unique = {}
    for candidate in candidates:
        key = (candidate.amount, candidate.currency)
        unique[key] = candidate

    if len(unique) == 1:
        return next(iter(unique.values()))
    return None
