"""ConversionRequest domain model."""

from dataclasses import dataclass
from typing import Dict
from src.models.currency_pair import CurrencyPair
from src.models.exchange_rate import ExchangeRate


@dataclass
class ConversionResult:
    """Represents the output of a processed conversion request."""

    request: "ConversionRequest"
    currency_pair: CurrencyPair
    converted_amount: float
    result_display: str
    pair_rate_display: str


@dataclass
class ConversionRequest:
    """Represents a request to convert an amount between two currencies."""

    amount: float
    source_currency: str
    target_currency: str

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if not self.source_currency or not self.target_currency:
            raise ValueError("Source and target currencies must be provided")

    def process(self, rates: Dict[str, ExchangeRate]) -> ConversionResult:
        """Process conversion request against exchange rates [FR-004, FR-017]."""
        if self.source_currency not in rates:
            raise ValueError(f"Rate for '{self.source_currency}' is not available.")
        if self.target_currency not in rates:
            raise ValueError(f"Rate for '{self.target_currency}' is not available.")

        rate_from = rates[self.source_currency]
        rate_to = rates[self.target_currency]
        pair = CurrencyPair(self.source_currency, self.target_currency, rate_from, rate_to)

        if self.source_currency == self.target_currency:
            converted = float(self.amount)
        else:
            converted = self.amount * rate_from.rate_per_unit / rate_to.rate_per_unit

        return ConversionResult(
            request=self,
            currency_pair=pair,
            converted_amount=converted,
            result_display=f"{converted:.2f}",
            pair_rate_display=pair.display,
        )
