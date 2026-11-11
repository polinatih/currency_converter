"""RateCache domain model."""

from dataclasses import dataclass, field
from typing import Dict
from src.models.exchange_rate import ExchangeRate


@dataclass
class RateCache:
    """Represents the persisted cached rates and metadata."""

    effective_date: str
    source_name: str
    rates: Dict[str, ExchangeRate] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize cache data to JSON-compatible dictionary."""
        rates_dict = {}
        for code, rate in self.rates.items():
            rates_dict[code] = {
                "currency_code": rate.currency_code,
                "rate_value": rate.rate_value,
                "nominal": rate.nominal,
                "effective_date": rate.effective_date,
                "source_name": rate.source_name,
            }
        return {
            "effective_date": self.effective_date,
            "source_name": self.source_name,
            "rates": rates_dict,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RateCache":
        """Deserialize cache data from dictionary."""
        rates = {}
        for code, rate_info in data.get("rates", {}).items():
            rates[code] = ExchangeRate(
                currency_code=rate_info["currency_code"],
                rate_value=float(rate_info["rate_value"]),
                nominal=int(rate_info.get("nominal", 1)),
                effective_date=rate_info.get("effective_date", data.get("effective_date", "")),
                source_name=rate_info.get("source_name", data.get("source_name", "BNM")),
                is_fallback=True,
            )
        return cls(
            effective_date=data.get("effective_date", ""),
            source_name=data.get("source_name", "BNM"),
            rates=rates,
        )
