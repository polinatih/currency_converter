"""ConversionRequest domain model."""

from dataclasses import dataclass


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
