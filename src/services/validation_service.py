"""Validation service for conversion inputs."""

from typing import Any, Tuple


class ValidationService:
    """Validates user inputs for conversion requests."""

    def validate_amount(self, value: Any) -> Tuple[bool, str]:
        """Validate that the amount is a positive number greater than zero.

        Returns (is_valid, error_message). When valid, error_message is empty.
        """
        if value is None:
            return False, "Amount cannot be empty."

        if isinstance(value, (int, float)):
            if value <= 0:
                return False, "Amount must be greater than zero."
            return True, ""

        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return False, "Amount cannot be empty."
            try:
                # Disallow multiple dots or invalid numeric strings
                amount = float(trimmed)
            except ValueError:
                return False, "Amount must be a valid positive number."

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
