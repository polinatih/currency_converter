"""Unit tests for input validation and same-currency handling.

Covers FR-003, FR-006, and FR-007.
"""

import unittest

from src.services.validation_service import ValidationService


class TestValidation(unittest.TestCase):
    """Validation test suite."""

    def setUp(self):
        self.validator = ValidationService()

    def test_empty_amount(self):
        """Empty or whitespace-only amount must be rejected with an error message."""
        for empty_val in ["", "   ", "\t", "\n", None]:
            is_valid, msg = self.validator.validate_amount(empty_val)
            self.assertFalse(is_valid, f"Expected {empty_val!r} to be invalid")
            self.assertTrue(len(msg) > 0, "Expected a non-empty error message")

    def test_zero_amount(self):
        """Zero amount must be rejected."""
        for zero_val in ["0", "0.0", "0.00", "000", 0, 0.0]:
            is_valid, msg = self.validator.validate_amount(zero_val)
            self.assertFalse(is_valid, f"Expected {zero_val!r} to be invalid")
            self.assertTrue(len(msg) > 0, "Expected a non-empty error message")

    def test_negative_amount(self):
        """Negative amounts must be rejected."""
        for neg_val in ["-1", "-0.01", "-100.50", -5, -0.001]:
            is_valid, msg = self.validator.validate_amount(neg_val)
            self.assertFalse(is_valid, f"Expected {neg_val!r} to be invalid")
            self.assertTrue(len(msg) > 0, "Expected a non-empty error message")

    def test_non_numeric_amount(self):
        """Non-numeric strings must be rejected."""
        for non_num in ["abc", "12a", "$100", "1.2.3", "one", "10,5"]:
            is_valid, msg = self.validator.validate_amount(non_num)
            self.assertFalse(is_valid, f"Expected {non_num!r} to be invalid")
            self.assertTrue(len(msg) > 0, "Expected a non-empty error message")

    def test_special_float_strings_and_exponential_rejected(self):
        """Strings like nan, inf, Infinity, 1_000, 1e3 must be rejected [FR-006]."""
        for invalid_val in ["nan", "inf", "NaN", "Infinity", "1_000", "1e3"]:
            is_valid, msg = self.validator.validate_amount(invalid_val)
            self.assertFalse(is_valid, f"Expected {invalid_val!r} to be rejected")
            self.assertTrue(len(msg) > 0, f"Expected error message for {invalid_val!r}")

    def test_valid_positive_amount(self):
        """Valid positive numeric amounts must be accepted."""
        for valid_val in ["100", "0.01", "123.45", "1000000", 50, 42.75]:
            is_valid, msg = self.validator.validate_amount(valid_val)
            self.assertTrue(is_valid, f"Expected {valid_val!r} to be valid, got: {msg}")
            self.assertEqual(msg, "")

    def test_validate_request_with_same_currency(self):
        """Identical source and target currencies must be accepted without error."""
        is_valid, msg = self.validator.validate_request("100", "USD", "USD")
        self.assertTrue(is_valid, f"Expected same-currency conversion to be valid, got: {msg}")
        self.assertEqual(msg, "")

        is_valid, msg = self.validator.validate_request("50.25", "MDL", "MDL")
        self.assertTrue(is_valid, f"Expected same-currency conversion to be valid, got: {msg}")
        self.assertEqual(msg, "")


    def test_surrounding_whitespace_is_allowed(self):
        """Spaces around a valid number are trimmed."""
        is_valid, msg = self.validator.validate_amount("  25.5  ")
        self.assertTrue(is_valid, msg)

    def test_comma_and_incomplete_decimals_rejected(self):
        """Only plain decimals with a dot are accepted (documented limitation)."""
        for value in ["10,5", ".5", "5.", "1 000", "+5"]:
            is_valid, msg = self.validator.validate_amount(value)
            self.assertFalse(is_valid, f"Expected {value!r} to be invalid")
            self.assertTrue(msg)

    def test_error_messages_are_specific(self):
        """Each kind of invalid input gets its own clear message (FR-012)."""
        self.assertEqual(self.validator.validate_amount("")[1], "Сумма не может быть пустой.")
        self.assertEqual(self.validator.validate_amount("0")[1], "Сумма должна быть больше нуля.")
        self.assertEqual(self.validator.validate_amount("-3")[1], "Сумма не может быть отрицательной.")
        self.assertEqual(self.validator.validate_amount("abc")[1], "Введите корректное положительное число.")

    def test_missing_currency_rejected(self):
        self.assertFalse(self.validator.validate_request("10", "", "MDL")[0])
        self.assertFalse(self.validator.validate_request("10", "USD", "  ")[0])

if __name__ == "__main__":
    unittest.main()
