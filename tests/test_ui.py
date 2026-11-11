"""UI tests for the Tkinter main window (T012-T021).

Separated from tests/test_rates.py so that a missing Tkinter / display only skips
these tests instead of masking failures in the service and parser tests.
"""

import os
import unittest
from unittest.mock import MagicMock
from urllib.error import URLError

from src.services.rate_service import RateResult, RateService

try:
    import tkinter as tk

    _probe = tk.Tk()
    _probe.destroy()
    TK_AVAILABLE, TK_SKIP_REASON = True, ""
except Exception as exc:  # no tkinter module or no display
    tk = None
    TK_AVAILABLE, TK_SKIP_REASON = False, f"Tkinter is not available: {exc}"

if TK_AVAILABLE:
    from src.ui.main_window import MainWindow


@unittest.skipUnless(TK_AVAILABLE, TK_SKIP_REASON)
class TestMainWindowT012T014(unittest.TestCase):
    """UI integration tests for T012, T013, T014 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-018]."""

    def setUp(self):
        self.mock_rate_service = MagicMock(spec=RateService)
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_bnm_response.xml"
        )
        with open(fixture_path, "r", encoding="utf-8") as f:
            self.sample_xml = f.read()

        real_service = RateService()
        rates, eff_date, src = real_service.parse_xml(self.sample_xml)
        self.mock_rate_service.get_rates_with_fallback.return_value = RateResult(
            rates=rates,
            effective_date=eff_date,
            source_name=src,
            is_fallback=False,
            notice="",
        )
        self.mock_rate_service.process_conversion_request = real_service.process_conversion_request
        self.mock_rate_service.convert = real_service.convert
        self.mock_rate_service.get_pair_rate_display = real_service.get_pair_rate_display
        self.mock_rate_service.format_result = real_service.format_result

        self.app = MainWindow(rate_service=self.mock_rate_service, async_load=False)
        self.app.withdraw()

    def tearDown(self):
        self.app.destroy()

    def test_currency_selectors_and_button_lifecycle(self):
        """Verify currency selectors, button disabled/enabled lifecycle, and converted display."""
        # T012: Currency selectors exist and contain loaded currencies
        self.assertTrue(any(v.startswith("USD") for v in self.app.src_currency_combo["values"]))
        self.assertTrue(any(v.startswith("EUR") for v in self.app.tgt_currency_combo["values"]))
        self.assertTrue(any(v.startswith("MDL") for v in self.app.tgt_currency_combo["values"]))

        # Button is disabled initially because amount is empty [FR-003]
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Invalid amount keeps button disabled [FR-003, FR-006]
        self.app.amount_var.set("invalid_amount")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Valid amount enables button [FR-003]
        self.app.amount_var.set("100")
        self.app.src_currency_var.set("USD")
        self.app.tgt_currency_var.set("EUR")
        self.assertEqual(str(self.app.convert_button["state"]), "normal")

        # T014: Click convert button
        self.app.on_convert()

        # T013: Display result (two decimals) and pair rate (four decimals), date and source [FR-005, FR-018]
        self.assertEqual(self.app.result_var.get(), "90.00 EUR")
        self.assertEqual(self.app.pair_rate_var.get(), "1 USD = 0.9000 EUR")
        self.assertIn("04.11.2026", self.app.info_var.get())
        self.assertIn("BNM", self.app.info_var.get())

        # Test currency swap button
        self.app.swap_button.invoke()
        self.assertEqual(self.app._get_code(self.app.src_currency_var.get()), "EUR")
        self.assertEqual(self.app._get_code(self.app.tgt_currency_var.get()), "USD")

        # Test Enter key triggers conversion
        self.app._on_enter_pressed()
        self.assertEqual(self.app.result_var.get(), "111.11 USD")

    def test_inline_validation_feedback_and_button_disabled(self):
        """Inline validation messages appear under amount for invalid inputs and clear on valid input [T015, T017]."""
        # Empty input: no error message, button disabled [FR-003]
        self.app.amount_var.set("")
        self.assertEqual(self.app.amount_error_var.get(), "")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Zero input: shows error message, button disabled [FR-006, FR-012]
        self.app.amount_var.set("0")
        self.assertEqual(self.app.amount_error_var.get(), "Сумма должна быть больше нуля.")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Negative input: shows error message, button disabled [FR-006, FR-012]
        self.app.amount_var.set("-10")
        self.assertEqual(self.app.amount_error_var.get(), "Сумма не может быть отрицательной.")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Non-numeric input: shows error message, button disabled [FR-006, FR-012]
        self.app.amount_var.set("abc")
        self.assertEqual(self.app.amount_error_var.get(), "Введите корректное положительное число.")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Special float string 'nan': shows error message, button disabled [FR-006, FR-012]
        self.app.amount_var.set("nan")
        self.assertEqual(self.app.amount_error_var.get(), "Введите корректное положительное число.")
        self.assertEqual(str(self.app.convert_button["state"]), "disabled")

        # Valid input: error message cleared, button enabled [FR-003]
        self.app.amount_var.set("50.25")
        self.assertEqual(self.app.amount_error_var.get(), "")
        self.assertEqual(str(self.app.convert_button["state"]), "normal")

    def test_same_currency_conversion_in_ui(self):
        """Identical currencies are handled without error in UI and return exact amount [T016, FR-007]."""
        self.app.amount_var.set("123.45")
        self.app.src_currency_var.set("USD")
        self.app.tgt_currency_var.set("USD")
        self.assertEqual(str(self.app.convert_button["state"]), "normal")

        self.app.on_convert()
        self.assertEqual(self.app.result_var.get(), "123.45 USD")
        self.assertEqual(self.app.pair_rate_var.get(), "1 USD = 1.0000 USD")
        self.assertIn("04.11.2026", self.app.info_var.get())
        self.assertIn("BNM", self.app.info_var.get())

    def test_t020_error_displayed_and_conversion_prevented_when_no_rates_available(self):
        """Display clear error and prevent conversion when source fails and no cache exists [T020, FR-009, FR-012]."""
        mock_svc = MagicMock(spec=RateService)
        mock_svc.get_rates_with_fallback.side_effect = URLError("Network unreachable and no cache")

        app = MainWindow(rate_service=mock_svc, async_load=False)
        app.withdraw()
        try:
            self.assertIn("Ошибка: не удалось получить курсы валют", app.status_var.get())
            app.amount_var.set("100")
            app.src_currency_var.set("USD")
            app.tgt_currency_var.set("MDL")
            app.on_convert()
            self.assertEqual(app.result_var.get(), "—")
        finally:
            app.destroy()

    def test_t021_explicit_notice_effective_date_and_source_displayed(self):
        """Show explicit latest-rate notice, effective date, and source when earlier rate used [T021, FR-005, FR-012, FR-015]."""
        mock_svc = MagicMock(spec=RateService)
        real_service = RateService()
        rates, _, _ = real_service.parse_xml(
            '<?xml version="1.0" encoding="UTF-8"?><ValCurs Date="02.11.2026" name="Official exchange rate"><Valute ID="44"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal><Name>US Dollar</Name><Value>18.0000</Value></Valute></ValCurs>'
        )
        mock_svc.get_rates_with_fallback.return_value = RateResult(
            rates=rates,
            effective_date="02.11.2026",
            source_name="BNM",
            is_fallback=True,
            notice="Используется курс на 02.11.2026.",
        )
        mock_svc.process_conversion_request = real_service.process_conversion_request

        app = MainWindow(rate_service=mock_svc, async_load=False)
        app.withdraw()
        try:
            info_text = app.info_var.get()
            self.assertIn("Используется курс на 02.11.2026.", info_text)
            self.assertIn("02.11.2026", info_text)
            self.assertIn("BNM", info_text)

            app.amount_var.set("100")
            app.src_currency_var.set("USD")
            app.tgt_currency_var.set("MDL")
            app.on_convert()

            info_after = app.info_var.get()
            self.assertIn("Используется курс на 02.11.2026.", info_after)
            self.assertIn("02.11.2026", info_after)
            self.assertIn("BNM", info_after)
        finally:
            app.destroy()

    def test_async_background_rate_loading(self):
        """Startup rate loading runs in a background thread and updates UI on completion."""
        mock_svc = MagicMock(spec=RateService)
        real_service = RateService()
        rates, eff_date, src = real_service.parse_xml(self.sample_xml)
        mock_svc.get_rates_with_fallback.return_value = RateResult(
            rates=rates,
            effective_date=eff_date,
            source_name=src,
            is_fallback=False,
            notice="",
        )
        app = MainWindow(rate_service=mock_svc, async_load=True)
        app.withdraw()
        try:
            if hasattr(app, "_load_thread"):
                app._load_thread.join(timeout=1.0)
            import time
            for _ in range(15):
                time.sleep(0.02)
                try:
                    app.update()
                except tk.TclError:
                    break
                if app.rate_result is not None:
                    break
            self.assertIsNotNone(app.rate_result)
            self.assertIn("04.11.2026", app.rate_meta_var.get())
        finally:
            app.destroy()


    def test_stale_result_cleared_when_input_changes(self):
        """manual fix: an old result must not stay on screen after the input changes."""
        self.app.amount_var.set("100")
        self.app.src_currency_var.set("USD")
        self.app.tgt_currency_var.set("EUR")
        self.app.on_convert()
        self.assertEqual(self.app.result_var.get(), "90.00 EUR")

        self.app.amount_var.set("0")
        self.assertEqual(self.app.result_var.get(), "—")
        self.assertEqual(self.app.pair_rate_var.get(), "")

    def test_offline_error_is_user_friendly(self):
        """manual fix: no raw exception text, pill switches from 'Загрузка…' to 'Нет данных'."""
        mock_svc = MagicMock(spec=RateService)
        mock_svc.get_rates_with_fallback.side_effect = URLError("[Errno 11001] getaddrinfo failed")
        app = MainWindow(rate_service=mock_svc, async_load=False)
        app.withdraw()
        try:
            status = app.status_var.get()
            self.assertIn("Ошибка: не удалось получить курсы валют", status)
            self.assertNotIn("Errno", status)
            self.assertNotIn("urlopen", status)
            self.assertEqual(str(app.convert_button["state"]), "disabled")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
