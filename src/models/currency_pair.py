"""CurrencyPair domain model."""

from dataclasses import dataclass
from src.models.exchange_rate import ExchangeRate


@dataclass
class CurrencyPair:
    """Represents a directional currency pair for conversion."""

    source_currency: str
    target_currency: str
    rate_from: ExchangeRate
    rate_to: ExchangeRate

    @property
    def pair_rate(self) -> float:
        """Units of target currency per 1 unit of source currency."""
        to_unit = self.rate_to.rate_per_unit
        if to_unit == 0:
            raise ZeroDivisionError("Target rate per unit cannot be zero")
        return self.rate_from.rate_per_unit / to_unit

    @property
    def display(self) -> str:
        """Formatted pair rate string: 1 <source> = X.XXXX <target>."""
        return f"1 {self.source_currency} = {self.pair_rate:.4f} {self.target_currency}"
