from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict

import requests


@dataclass
class FxConverter:
    cache: Dict[str, float] = field(default_factory=dict)

    def to_eur(self, amount: float, currency: str) -> float:
        currency = currency.upper()
        if currency == "EUR":
            return amount
        rate = self._get_rate(currency)
        return amount * rate

    def _get_rate(self, currency: str) -> float:
        if currency in self.cache:
            return self.cache[currency]
        url = "https://api.exchangerate.host/latest"
        params = {"base": currency, "symbols": "EUR"}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            rate = data["rates"]["EUR"]
            self.cache[currency] = rate
            return rate
        except (requests.RequestException, KeyError, ValueError):
            logging.exception("Failed to fetch FX rate for %s", currency)
            raise
