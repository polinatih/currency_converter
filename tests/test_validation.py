"""Unit tests for input validation and same-currency handling.

Covers FR-003, FR-006, and FR-007.
"""

import unittest

try:
    from src.services.validation_service import ValidationService
except ImportError:
    ValidationService = None


class TestValidation(unittest.TestCase):
    """Validation test suite."""

    def setUp(self):
        if ValidationService is None:
            self.fail("ValidationService is not implemented yet")
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

    def test_same_currency_returns_original_amount(self):
        """Same-currency conversion must return exactly the original amount."""
        amount = 123.45
        result = self.validator.convert_same_currency(amount, "EUR", "EUR")
        self.assertEqual(result, 123.45)

        # Also test with float/str conversions
        result_str = self.validator.format_same_currency(100.0, "USD")
        self.assertEqual(result_str, "100.00")


if __name__ == "__main__":
    unittest.main()
