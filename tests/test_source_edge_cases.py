"""Additional unit tests for the data source and conversion (stage 3, test/unit-tests).

Part 6 of the assignment requires coverage of:
- parsing the source response,
- conversion in both directions,
- empty or invalid source responses,
- user input validation (see tests/test_validation.py).

Network access is never used: fetch_xml_from_bnm is always mocked.
"""

import os
import tempfile
import unittest
from datetime import date
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET

from src.services.cache_service import CacheService
from src.services.rate_service import RateService

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_bnm_response.xml")


def _xml(*valutes, date_str="11.11.2026"):
    body = "".join(
        "<Valute><CharCode>{}</CharCode><Nominal>{}</Nominal><Name>{}</Name><Value>{}</Value></Valute>".format(*v)
        for v in valutes
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><ValCurs Date="{date_str}" name="Official exchange rate">{body}</ValCurs>'


class TestParsing(unittest.TestCase):
    """Parsing of the BNM XML response."""

    def setUp(self):
        self.service = RateService(cache_service=CacheService(cache_path=os.devnull))
        with open(FIXTURE, encoding="utf-8") as f:
            self.sample = f.read()

    def test_all_fixture_currencies_parsed(self):
        rates, eff, src = self.service.parse_xml(self.sample)
        self.assertEqual(set(rates), {"USD", "EUR", "HUF", "RON", "GBP", "MDL"})
        self.assertEqual((eff, src), ("04.11.2026", "BNM"))

    def test_currency_name_is_kept(self):
        rates, _, _ = self.service.parse_xml(self.sample)
        self.assertEqual(rates["USD"].currency_name, "US Dollar")

    def test_comma_decimal_separator_in_value(self):
        rates, _, _ = self.service.parse_xml(_xml(("USD", 1, "US Dollar", "17,9458")))
        self.assertAlmostEqual(rates["USD"].rate_value, 17.9458)

    def test_rate_per_unit_uses_nominal(self):
        rates, _, _ = self.service.parse_xml(self.sample)
        self.assertAlmostEqual(rates["HUF"].rate_per_unit, 0.05)
        self.assertAlmostEqual(rates["USD"].rate_per_unit, 18.0)

    def test_entries_with_broken_values_are_skipped(self):
        xml = _xml(
            ("USD", 1, "US Dollar", "18.0000"),
            ("XXX", 1, "Bad value", "abc"),
            ("YYY", "ten", "Bad nominal", "1.0"),
        )
        rates, _, _ = self.service.parse_xml(xml)
        self.assertIn("USD", rates)
        self.assertNotIn("XXX", rates)
        self.assertNotIn("YYY", rates)

    def test_zero_negative_or_missing_rate_is_skipped(self):
        """data-model.md: rate values and nominal MUST be numeric and positive."""
        xml = (
            '<ValCurs Date="11.11.2026">'
            "<Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>18.0</Value></Valute>"
            "<Valute><CharCode>ZER</CharCode><Nominal>1</Nominal><Value>0</Value></Valute>"
            "<Valute><CharCode>NEG</CharCode><Nominal>1</Nominal><Value>-5</Value></Valute>"
            "<Valute><CharCode>NOV</CharCode><Nominal>1</Nominal></Valute>"
            "<Valute><CharCode>NOM</CharCode><Nominal>0</Nominal><Value>5</Value></Valute>"
            "</ValCurs>"
        )
        rates, _, _ = self.service.parse_xml(xml)
        self.assertIn("USD", rates)
        for bad in ("ZER", "NEG", "NOV", "NOM"):
            self.assertNotIn(bad, rates, f"{bad} must be skipped")


class TestConversionBothDirections(unittest.TestCase):
    """Conversion in both directions, including cross rates through MDL."""

    def setUp(self):
        self.service = RateService(cache_service=CacheService(cache_path=os.devnull))
        with open(FIXTURE, encoding="utf-8") as f:
            self.rates, _, _ = self.service.parse_xml(f.read())

    def test_round_trip_returns_original_amount(self):
        for a, b in [("USD", "MDL"), ("EUR", "USD"), ("HUF", "GBP"), ("MDL", "RON")]:
            there = self.service.convert(250.0, a, b, self.rates)
            back = self.service.convert(there, b, a, self.rates)
            self.assertAlmostEqual(back, 250.0, places=9, msg=f"{a}->{b}->{a}")

    def test_pair_rates_are_reciprocal(self):
        fwd = self.service.convert(1.0, "GBP", "EUR", self.rates)
        rev = self.service.convert(1.0, "EUR", "GBP", self.rates)
        self.assertAlmostEqual(fwd * rev, 1.0, places=12)

    def test_cross_rate_with_nominal(self):
        # 1000 HUF = 50 MDL; 50 MDL / 20 MDL per EUR = 2.5 EUR
        self.assertAlmostEqual(self.service.convert(1000.0, "HUF", "EUR", self.rates), 2.5)
        self.assertAlmostEqual(self.service.convert(2.5, "EUR", "HUF", self.rates), 1000.0)

    def test_unknown_currency_raises(self):
        with self.assertRaises(ValueError):
            self.service.convert(10.0, "USD", "JPY", self.rates)


class TestEmptyAndInvalidResponses(unittest.TestCase):
    """Empty or invalid responses from the source."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = CacheService(cache_path=os.path.join(self.tmp.name, "c.json"))
        self.service = RateService(cache_service=self.cache)
        self.good = _xml(("USD", 1, "US Dollar", "18.0"), date_str="09.11.2026")

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_string_is_an_error(self):
        with self.assertRaises(ET.ParseError):
            self.service.parse_xml("")

    def test_html_error_page_is_not_treated_as_empty_day(self):
        """A non-BNM document (e.g. an HTML error page) is an invalid response, not 'no rates today'."""
        html = "<html><body>Service unavailable</body></html>"
        self.assertFalse(self.service.is_empty_response(html))
        with self.assertRaises(ET.ParseError):
            self.service.parse_xml(html)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_html_error_page_falls_back_to_cache_without_date_search(self, mock_fetch):
        rates, eff, src = self.service.parse_xml(self.good)
        self.cache.save_cache(eff, src, rates)
        mock_fetch.return_value = "<html><body>Service unavailable</body></html>"

        result = self.service.get_rates_with_fallback(date(2026, 11, 11))
        self.assertEqual(mock_fetch.call_count, 1)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "09.11.2026")

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_weekend_uses_friday_rate(self, mock_fetch):
        """Sunday and Saturday are empty -> Friday's rate is used and reported."""
        empty = _xml(date_str="")
        friday = _xml(("USD", 1, "US Dollar", "17.9"), date_str="06.11.2026")
        mock_fetch.side_effect = lambda d: friday if d == "06.11.2026" else empty

        result = self.service.get_rates_with_fallback(date(2026, 11, 8))  # Sunday
        self.assertEqual(mock_fetch.call_count, 3)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "06.11.2026")
        self.assertIn("06.11.2026", result.notice)

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_timeout_falls_back_to_cache(self, mock_fetch):
        rates, eff, src = self.service.parse_xml(self.good)
        self.cache.save_cache(eff, src, rates)
        mock_fetch.side_effect = TimeoutError("timed out")

        result = self.service.get_rates_with_fallback(date(2026, 11, 11))
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.effective_date, "09.11.2026")

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_successful_response_updates_cache(self, mock_fetch):
        mock_fetch.return_value = _xml(("USD", 1, "US Dollar", "18.1"), date_str="11.11.2026")
        self.service.get_rates_with_fallback(date(2026, 11, 11))
        self.assertEqual(self.cache.load_cache()["effective_date"], "11.11.2026")

    @patch.object(RateService, "fetch_xml_from_bnm")
    def test_network_error_does_not_touch_cache(self, mock_fetch):
        rates, eff, src = self.service.parse_xml(self.good)
        self.cache.save_cache(eff, src, rates)
        mock_fetch.side_effect = URLError("offline")
        self.service.get_rates_with_fallback(date(2026, 11, 11))
        self.assertEqual(self.cache.load_cache()["effective_date"], "09.11.2026")

    def test_corrupted_cache_file_is_ignored(self):
        with open(self.cache.cache_path, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertIsNone(self.cache.load_cache())


if __name__ == "__main__":
    unittest.main()
