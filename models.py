from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SourcePrice:
    url: str
    price_original: float
    currency: str
    price_eur: float


@dataclass
class Result:
    sources: List[SourcePrice]
    min_eur: Optional[float]
    median_eur: Optional[float]
    max_eur: Optional[float]
    reliability: str
