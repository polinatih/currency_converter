"""Unit tests for exchange rate fetching, parsing, conversion, fallback, and caching.

Covers T003, T004, and T005 [FR-004, FR-008, FR-009, FR-010, FR-011, FR-013, FR-014, FR-015,
FR-016, FR-017, FR-018, FR-019, FR-020].
"""

import io
import json
import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, call, patch
from urllib.error import URLError

try:
    from src.models.conversion_request import ConversionRequest, ConversionResult
    from src.models.currency_pair import CurrencyPair
    from src.models.exchange_rate import ExchangeRate
    from src.services.cache_service import CacheService
    from src.services.rate_service import RateResult, RateService
    from src.ui.main_window import MainWindow
except ImportError:
    ConversionRequest = None
    ConversionResult = None
    CurrencyPair = None
    ExchangeRate = None
    CacheService = None
    RateResult = None
    RateService = None
    MainWindow = None


class TestRatesT003(unittest.TestCase):
    """Tests for T003 [US1]: XML parsing, conversions, pair-rate, result format, timeout."""

    def setUp(self):
        if RateService is None:
            self.fail("RateService is not implemented yet")
        self.service = RateService()
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_bnm_response.xml"
        )
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            self.sample_xml = f.read()

    def test_parse_bnm_xml(self):
        """Parse BNM XML and verify extracted rates, including synthetic MDL rate."""
        rates, effective_date, source_name = self.service.parse_xml(self.sample_xml)
        self.assertEqual(source_name, "BNM")
        self.assertEqual(effective_date, "04.11.2026")

        # Verify USD
        self.assertIn("USD", rates)
        self.assertEqual(rates["USD"].currency_code, "USD")
        self.assertAlmostEqual(rates["USD"].rate_value, 18.0)
        self.assertEqual(rates["USD"].nominal, 1)

        # Verify EUR
        self.assertIn("EUR", rates)
        self.assertEqual(rates["EUR"].currency_code, "EUR")
        self.assertAlmostEqual(rates["EUR"].rate_value, 20.0)
        self.assertEqual(rates["EUR"].nominal, 1)

        # Verify HUF with nominal 100
        self.assertIn("HUF", rates)
        self.assertEqual(rates["HUF"].nominal, 100)
        self.assertAlmostEqual(rates["HUF"].rate_value, 5.0)

        # Verify synthetic MDL rate (rate 1.0, nominal 1)
        self.assertIn("MDL", rates)
        self.assertEqual(rates["MDL"].currency_code, "MDL")
        self.assertAlmostEqual(rates["MDL"].rate_value, 1.0)
        self.assertEqual(rates["MDL"].nominal, 1)

    def test_nominal_handling(self):
        """Rate per nominal unit must divide rate_value by nominal."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        # HUF rate_value = 5.0, nominal = 100 -> 0.05 MDL per 1 HUF
        huf_rate = rates["HUF"]
        rate_per_unit = huf_rate.rate_value / huf_rate.nominal
        self.assertAlmostEqual(rate_per_unit, 0.05)

    def test_conversion_usd_to_mdl(self):
        """Converting USD to MDL: 100 USD = 1800.00 MDL."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(100.0, "USD", "MDL", rates)
        self.assertAlmostEqual(result, 1800.0, places=2)

    def test_conversion_mdl_to_usd(self):
        """Converting MDL to USD: 100 MDL = 5.56 USD (100 / 18)."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(100.0, "MDL", "USD", rates)
        self.assertAlmostEqual(result, 5.56, places=2)

    def test_conversion_usd_to_eur(self):
        """Converting USD to EUR: 100 USD (18.0) -> 90.00 EUR (20.0)."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(100.0, "USD", "EUR", rates)
        self.assertAlmostEqual(result, 90.0, places=2)

    def test_conversion_eur_to_usd(self):
        """Converting EUR to USD: 100 EUR (20.0) -> 111.11 USD (18.0)."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(100.0, "EUR", "USD", rates)
        self.assertAlmostEqual(result, 111.11, places=2)

    def test_conversion_with_nominal_currency(self):
        """Converting HUF (nominal 100, val 5) to MDL: 1000 HUF = 50.00 MDL."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(1000.0, "HUF", "MDL", rates)
        self.assertAlmostEqual(result, 50.0, places=2)

    def test_conversion_same_currency(self):
        """Converting same currency returns exactly the original amount and formats correctly."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        result = self.service.convert(123.45, "EUR", "EUR", rates)
        self.assertEqual(result, 123.45)
        self.assertEqual(self.service.format_result(result), "123.45")

    def test_conversion_request_processing(self):
        """ConversionRequest.process and service.process_conversion_request calculate amounts and pair rates [T011]."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)
        req = ConversionRequest(100.0, "USD", "EUR")
        result = req.process(rates)
        self.assertAlmostEqual(result.converted_amount, 90.0)
        self.assertEqual(result.result_display, "90.00")
        self.assertEqual(result.pair_rate_display, "1 USD = 0.9000 EUR")

        # Via service
        svc_result = self.service.process_conversion_request(req, rates)
        self.assertEqual(svc_result.result_display, "90.00")
        self.assertEqual(svc_result.pair_rate_display, "1 USD = 0.9000 EUR")

    def test_pair_rate_display_four_decimals(self):
        """Display pair rate as '1 <source> = X <target>' with 4 decimal places."""
        rates, _, _ = self.service.parse_xml(self.sample_xml)

        pair_usd_eur = self.service.get_pair_rate_display("USD", "EUR", rates)
        self.assertEqual(pair_usd_eur, "1 USD = 0.9000 EUR")

        pair_eur_usd = self.service.get_pair_rate_display("EUR", "USD", rates)
        self.assertEqual(pair_eur_usd, "1 EUR = 1.1111 USD")

        pair_usd_mdl = self.service.get_pair_rate_display("USD", "MDL", rates)
        self.assertEqual(pair_usd_mdl, "1 USD = 18.0000 MDL")

        pair_mdl_usd = self.service.get_pair_rate_display("MDL", "USD", rates)
        self.assertEqual(pair_mdl_usd, "1 MDL = 0.0556 USD")

    def test_result_display_two_decimals(self):
        """Converted result must be formatted with two decimal places."""
        self.assertEqual(self.service.format_result(1800.0), "1800.00")
        self.assertEqual(self.service.format_result(5.5555), "5.56")
        self.assertEqual(self.service.format_result(90.0), "90.00")
        self.assertEqual(self.service.format_result(111.1111), "111.11")

    @patch("urllib.request.urlopen")
    def test_urllib_request_10_second_timeout(self, mock_urlopen):
        """Requests must use urllib with a 10-second timeout."""
        mock_response = MagicMock()
        mock_response.read.return_value = self.sample_xml.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        self.service.fetch_xml_from_bnm("04.11.2026")
        mock_urlopen.assert_called_once()
        _, kwargs = mock_urlopen.call_args
        self.assertEqual(kwargs.get("timeout"), 10)


class TestRatesT004(unittest.TestCase):
    """Tests for T004 [US2]: empty responses, malformed XML, date-by-date fallback."""

    def setUp(self):
        if RateService is None:
            self.fail("RateService is not implemented yet")
        self.service = RateService()
        self.empty_xml = '<?xml version="1.0" encoding="UTF-8"?><ValCurs Date="04.11.2026" name="Official exchange rate"></ValCurs>'
        self.valid_xml = '<?xml version="1.0" encoding="UTF-8"?><ValCurs Date="02.11.2026" name="Official exchange rate"><Valute ID="44"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal><Name>US Dollar</Name><Value>18.0000</Value></Valute></ValCurs>'
        self.malformed_xml = "<ValCurs Date='04.11.2026'><Valute>broken xml without closing tags"

    def test_empty_xml_response_detected(self):
        """An XML response with no Valute elements must be recognized as empty."""
        rates, effective_date, source_name = self.service.parse_xml(self.empty_xml)
        # Rates should contain only MDL or be empty of foreign currencies
        foreign_rates = {k: v for k, v in rates.items() if k != "MDL"}
        self.assertEqual(len(foreign_rates), 0)
        self.assertTrue(self.service.is_empty_response(self.empty_xml))

    def test_malformed_xml_raises_error(self):
        """Malformed XML must raise an error and not be treated as empty or valid."""
        with self.assertRaises(Exception):
            self.service.parse_xml(self.malformed_xml)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_date_by_date_fallback_success(self, mock_fetch):
        """Empty response for today and yesterday should fall back to 2 days ago."""
        today = date(2026, 11, 4)
        day_1 = today - timedelta(days=1)
        day_2 = today - timedelta(days=2)

        def side_effect(date_str):
            if date_str == today.strftime("%d.%m.%Y"):
                return self.empty_xml
            elif date_str == day_1.strftime("%d.%m.%Y"):
                return self.empty_xml
            elif date_str == day_2.strftime("%d.%m.%Y"):
                return self.valid_xml
            return self.empty_xml

        mock_fetch.side_effect = side_effect

        result = self.service.get_rates_with_fallback(today)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "02.11.2026")
        self.assertIn("USD", result.rates)
        self.assertIn("02.11.2026", result.notice)
        self.assertEqual(mock_fetch.call_count, 3)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_date_by_date_fallback_exhausted_10_days(self, mock_fetch):
        """Checking today and 10 previous days (11 total) must stop and report no rates."""
        today = date(2026, 11, 15)
        mock_fetch.return_value = self.empty_xml

        result = self.service.get_rates_with_fallback(today, use_cache=False)
        self.assertEqual(mock_fetch.call_count, 11)
        self.assertIsNone(result)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_malformed_xml_does_not_continue_date_search(self, mock_fetch):
        """Malformed XML is an error; it must not trigger calendar date iteration."""
        today = date(2026, 11, 4)
        mock_fetch.return_value = self.malformed_xml

        with self.assertRaises(Exception):
            self.service.get_rates_with_fallback(today, use_cache=False)
        self.assertEqual(mock_fetch.call_count, 1)


class TestRatesT005(unittest.TestCase):
    """Tests for T005 [US2]: JSON cache persistence, preservation, and fallback."""

    def setUp(self):
        if RateService is None or CacheService is None:
            self.fail("RateService or CacheService is not implemented yet")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_file = os.path.join(self.temp_dir.name, "rates_cache.json")
        self.cache_service = CacheService(cache_path=self.cache_file)
        self.rate_service = RateService(cache_service=self.cache_service)
        self.valid_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ValCurs Date="01.11.2026" name="Official exchange rate">'
            '<Valute ID="44"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal><Name>US Dollar</Name><Value>18.0000</Value></Valute>'
            '</ValCurs>'
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_persistence_across_restart(self):
        """Saving successful rates must survive and load in a fresh CacheService."""
        rates, effective_date, source_name = self.rate_service.parse_xml(self.valid_xml)
        self.cache_service.save_cache(effective_date, source_name, rates)

        self.assertTrue(os.path.exists(self.cache_file))

        # Simulate restart with fresh CacheService instance
        fresh_cache = CacheService(cache_path=self.cache_file)
        cached_data = fresh_cache.load_cache()

        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["effective_date"], "01.11.2026")
        self.assertEqual(cached_data["source_name"], "BNM")
        self.assertIn("USD", cached_data["rates"])
        self.assertEqual(cached_data["rates"]["USD"]["rate_value"], 18.0)
        self.assertEqual(cached_data["rates"]["USD"]["nominal"], 1)

    def test_cache_not_overwritten_by_empty_or_malformed(self):
        """Empty, malformed, or failed responses must never overwrite valid cache."""
        rates, effective_date, source_name = self.rate_service.parse_xml(self.valid_xml)
        self.cache_service.save_cache(effective_date, source_name, rates)

        # Attempt to save empty rates
        self.cache_service.save_cache_if_valid("02.11.2026", "BNM", {})
        cached_data = self.cache_service.load_cache()
        self.assertEqual(cached_data["effective_date"], "01.11.2026")

        # Attempt to save None or invalid
        self.cache_service.save_cache_if_valid("02.11.2026", "BNM", None)
        cached_data = self.cache_service.load_cache()
        self.assertEqual(cached_data["effective_date"], "01.11.2026")

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_fallback_to_cache_on_network_error(self, mock_fetch):
        """Network error must fall back to cached rates with effective date shown."""
        rates, effective_date, source_name = self.rate_service.parse_xml(self.valid_xml)
        self.cache_service.save_cache(effective_date, source_name, rates)

        mock_fetch.side_effect = URLError("Network unreachable")

        today = date(2026, 11, 4)
        result = self.rate_service.get_rates_with_fallback(today)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "01.11.2026")
        self.assertEqual(result.source_name, "BNM")
        self.assertIn("01.11.2026", result.notice)
        self.assertIn("USD", result.rates)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_fallback_to_cache_on_malformed_xml(self, mock_fetch):
        """Malformed XML must fall back to cached rates when available."""
        rates, effective_date, source_name = self.rate_service.parse_xml(self.valid_xml)
        self.cache_service.save_cache(effective_date, source_name, rates)

        mock_fetch.return_value = "<broken><xml>"

        today = date(2026, 11, 4)
        result = self.rate_service.get_rates_with_fallback(today)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "01.11.2026")
        self.assertIn("01.11.2026", result.notice)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_failure_when_no_cache_and_network_fails(self, mock_fetch):
        """When network fails and no cache exists, must raise error / prevent conversion."""
        mock_fetch.side_effect = URLError("Network unreachable")
        today = date(2026, 11, 4)

        with self.assertRaises(Exception):
            self.rate_service.get_rates_with_fallback(today)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_fallback_to_cache_when_10_day_search_empty(self, mock_fetch):
        """When 10-day search finds no rates but network works, notice must not say 'Network/source unavailable' [US2]."""
        rates, effective_date, source_name = self.rate_service.parse_xml(self.valid_xml)
        self.cache_service.save_cache(effective_date, source_name, rates)

        # Network returns well-formed but empty XML for all dates
        empty_xml = '<?xml version="1.0" encoding="UTF-8"?><ValCurs Date="04.11.2026" name="Official exchange rate"></ValCurs>'
        mock_fetch.return_value = empty_xml

        today = date(2026, 11, 15)
        result = self.rate_service.get_rates_with_fallback(today)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "01.11.2026")
        self.assertIn("01.11.2026", result.notice)
        self.assertNotIn("Network/source unavailable", result.notice)
        self.assertIn("Нет опубликованных курсов за последние 10 дней", result.notice)


class TestMainWindowT012T014(unittest.TestCase):
    """UI integration tests for T012, T013, T014 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-018]."""

    def setUp(self):
        if MainWindow is None or RateService is None:
            self.fail("MainWindow or RateService is not implemented")

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


if __name__ == "__main__":
    unittest.main()
