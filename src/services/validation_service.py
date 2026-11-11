"""Validation service for conversion inputs."""

import math
import re
from typing import Any, Tuple


DECIMAL_PATTERN = re.compile(r"^\d+(\.\d+)?$")


class ValidationService:
    """Validates user inputs for conversion requests."""

    def validate_amount(self, value: Any) -> Tuple[bool, str]:
        """Validate that the amount is a positive plain decimal number greater than zero.

        Rejects non-numeric characters, letters (including 'nan', 'inf', 'e'),
        underscores, negative values, and zero [FR-006].
        Returns (is_valid, error_message). When valid, error_message is empty.
        """
        if value is None:
            return False, "Amount cannot be empty."

        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                return False, "Amount must be a finite number."
            if value <= 0:
                return False, "Amount must be greater than zero."
            return True, ""

        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return False, "Amount cannot be empty."

            if trimmed.startswith("-"):
                return False, "Amount cannot be negative."

            if not DECIMAL_PATTERN.match(trimmed):
                return False, "Amount must be a valid positive number."

            try:
                amount = float(trimmed)
            except ValueError:
                return False, "Amount must be a valid positive number."

            if not math.isfinite(amount):
                return False, "Amount must be a finite number."

            if amount <= 0:
                return False, "Amount must be greater than zero."

            return True, ""

        return False, "Invalid amount type."

    def validate_request(self, amount: Any, source_currency: str, target_currency: str) -> Tuple[bool, str]:
        """Validate amount and currency selection.

        Identical source and target currencies are valid [FR-007].
        """
        is_valid, msg = self.validate_amount(amount)
        if not is_valid:
            return False, msg

        if not source_currency or not str(source_currency).strip():
            return False, "Source currency must be selected."

        if not target_currency or not str(target_currency).strip():
            return False, "Target currency must be selected."

        return True, ""
