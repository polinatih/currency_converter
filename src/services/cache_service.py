"""Cache service for persisting the last successful exchange rates to a JSON file."""

import json
import os
from typing import Any, Dict, Optional
from src.models.exchange_rate import ExchangeRate


DEFAULT_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "rates_cache.json",
)


class CacheService:
    """Manages the local single JSON cache file for exchange rates."""

    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = cache_path or DEFAULT_CACHE_FILE

    def save_cache(self, effective_date: str, source_name: str, rates: Dict[str, Any]) -> None:
        """Save the exchange rate data to the local JSON cache file."""
        rates_data = {}
        for code, rate in rates.items():
            if isinstance(rate, ExchangeRate):
                rates_data[code] = {
                    "currency_code": rate.currency_code,
                    "rate_value": rate.rate_value,
                    "nominal": rate.nominal,
                    "effective_date": rate.effective_date,
                    "source_name": rate.source_name,
                    "currency_name": rate.currency_name,
                }
            elif isinstance(rate, dict):
                rates_data[code] = {
                    "currency_code": rate.get("currency_code", code),
                    "rate_value": float(rate["rate_value"]),
                    "nominal": int(rate.get("nominal", 1)),
                    "effective_date": rate.get("effective_date", effective_date),
                    "source_name": rate.get("source_name", source_name),
                    "currency_name": rate.get("currency_name", ""),
                }

        payload = {
            "effective_date": effective_date,
            "source_name": source_name,
            "rates": rates_data,
        }

        os.makedirs(os.path.dirname(os.path.abspath(self.cache_path)), exist_ok=True)
        # Write to temporary file first or atomic overwrite
        temp_file = f"{self.cache_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, self.cache_path)

    def save_cache_if_valid(self, effective_date: str, source_name: str, rates: Any) -> bool:
        """Save only if the response is non-empty and valid.

        Empty, malformed, or failed responses must never overwrite an existing cache [FR-011, FR-019].
        """
        if not rates or not isinstance(rates, dict):
            return False

        # Must have at least foreign currency rates (not just empty or only MDL)
        foreign_rates = [k for k in rates.keys() if k != "MDL"]
        if not foreign_rates:
            return False

        self.save_cache(effective_date, source_name, rates)
        return True

    def load_cache(self) -> Optional[dict]:
        """Load the cached rates from JSON file. Returns None if absent or invalid."""
        if not os.path.exists(self.cache_path):
            return None

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return None
            if "effective_date" not in data or "rates" not in data:
                return None
            return data
        except (json.JSONDecodeError, OSError):
            return None
