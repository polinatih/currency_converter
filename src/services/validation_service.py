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
            return False, "Сумма не может быть пустой."

        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                return False, "Число должно быть конечным."
            if value <= 0:
                return False, "Сумма должна быть больше нуля."
            return True, ""

        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return False, "Сумма не может быть пустой."

            if trimmed.startswith("-"):
                return False, "Сумма не может быть отрицательной."

            if not DECIMAL_PATTERN.match(trimmed):
                return False, "Введите корректное положительное число."

            try:
                amount = float(trimmed)
            except ValueError:
                return False, "Введите корректное положительное число."

            if not math.isfinite(amount):
                return False, "Число должно быть конечным."

            if amount <= 0:
                return False, "Сумма должна быть больше нуля."

            return True, ""

        return False, "Неверный тип суммы."

    def validate_request(self, amount: Any, source_currency: str, target_currency: str) -> Tuple[bool, str]:
        """Validate amount and currency selection.

        Identical source and target currencies are valid [FR-007].
        """
        is_valid, msg = self.validate_amount(amount)
        if not is_valid:
            return False, msg

        if not source_currency or not str(source_currency).strip():
            return False, "Выберите исходную валюту."

        if not target_currency or not str(target_currency).strip():
            return False, "Выберите целевую валюту."

        return True, ""
