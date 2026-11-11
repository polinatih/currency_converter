"""ExchangeRate domain model."""

from dataclasses import dataclass


@dataclass
class ExchangeRate:
    """Represents an exchange rate for a currency relative to MDL."""

    currency_code: str
    rate_value: float
    nominal: int = 1
    effective_date: str = ""
    source_name: str = "BNM"
    is_fallback: bool = False
    currency_name: str = ""

    @property
    def target_currency(self) -> str:
        """Alias for currency_code matching data-model specification."""
        return self.currency_code

    @property
    def rate_per_unit(self) -> float:
        """MDL per single currency unit."""
        if self.nominal == 0:
            raise ValueError("Nominal cannot be zero")
        return self.rate_value / self.nominal

    @classmethod
    def create_mdl_rate(
        cls,
        effective_date: str = "",
        source_name: str = "BNM",
        currency_name: str = "Молдавский лей",
    ) -> "ExchangeRate":
        """Factory for the synthetic MDL exchange rate (rate 1, nominal 1)."""
        return cls(
            currency_code="MDL",
            rate_value=1.0,
            nominal=1,
            effective_date=effective_date,
            source_name=source_name,
            is_fallback=False,
            currency_name=currency_name,
        )
