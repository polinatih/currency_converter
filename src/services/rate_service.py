"""Rate service for fetching, parsing, converting, and falling back on exchange rates."""

import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Optional, Tuple
import xml.etree.ElementTree as ET

from src.models.conversion_request import ConversionRequest, ConversionResult
from src.models.exchange_rate import ExchangeRate
from src.services.cache_service import CacheService


BNM_URL_TEMPLATE = "https://www.bnm.md/en/official_exchange_rates?get_xml=1&date={date_str}"


@dataclass
class RateResult:
    """Result of rate retrieval including metadata and fallback notices."""

    rates: Dict[str, ExchangeRate]
    effective_date: str
    source_name: str
    is_fallback: bool = False
    notice: str = ""


class RateService:
    """Retrieves and manages exchange rates from BNM feed and local cache."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()

    def fetch_xml_from_bnm(self, date_str: str) -> str:
        """Fetch raw XML from BNM endpoint with a 10-second timeout [FR-020]."""
        url = BNM_URL_TEMPLATE.format(date_str=date_str)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CurrencyConverter/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode("utf-8")

    def parse_xml(self, xml_content: str) -> Tuple[Dict[str, ExchangeRate], str, str]:
        """Parse BNM XML content and return (rates, effective_date, source_name).

        Normalizes rates to MDL per one unit (rate_value / nominal, MDL = 1) [FR-016].
        """
        root = self._parse_root(xml_content)
        effective_date = root.attrib.get("Date", "").strip()
        source_name = "BNM"

        rates: Dict[str, ExchangeRate] = {}

        for valute in root.findall("Valute"):
            char_code = (valute.findtext("CharCode") or "").strip()
            nominal_str = (valute.findtext("Nominal") or "1").strip()
            value_str = (valute.findtext("Value") or "").strip().replace(",", ".")

            if not char_code:
                continue

            try:
                nominal = int(nominal_str)
                rate_value = float(value_str)
            except ValueError:
                continue

            # data-model.md: rate value and nominal MUST be positive
            if rate_value <= 0 or nominal <= 0:
                continue

            name = (valute.findtext("Name") or "").strip()

            rates[char_code] = ExchangeRate(
                currency_code=char_code,
                rate_value=rate_value,
                nominal=nominal,
                effective_date=effective_date,
                source_name=source_name,
                is_fallback=False,
                currency_name=name,
            )

        # Synthetic MDL rate [FR-016]
        rates["MDL"] = ExchangeRate.create_mdl_rate(
            effective_date=effective_date,
            source_name=source_name,
            currency_name="Молдавский лей",
        )

        return rates, effective_date, source_name

    @staticmethod
    def _parse_root(xml_content: str) -> ET.Element:
        """Parse XML and make sure it is a BNM <ValCurs> document.

        Any other document (e.g. an HTML error page) is treated as malformed,
        not as an empty publication day.
        """
        root = ET.fromstring(xml_content)
        if root.tag != "ValCurs":
            raise ET.ParseError(f"Unexpected root element <{root.tag}>, expected <ValCurs>")
        return root

    def is_empty_response(self, xml_content: str) -> bool:
        """Check if a valid BNM document has no Valute elements."""
        try:
            root = self._parse_root(xml_content)
            return len(root.findall("Valute")) == 0
        except ET.ParseError:
            return False

    def convert(
        self,
        amount: float,
        source_currency: str,
        target_currency: str,
        rates: Dict[str, ExchangeRate],
    ) -> float:
        """Convert amount between currencies using per-unit rates [FR-004, FR-017].

        Same-currency conversion returns the original amount [FR-007].
        """
        if source_currency == target_currency:
            return float(amount)

        if source_currency not in rates:
            raise ValueError(f"Rate for currency '{source_currency}' is not available.")
        if target_currency not in rates:
            raise ValueError(f"Rate for currency '{target_currency}' is not available.")

        unit_from = rates[source_currency].rate_per_unit
        unit_to = rates[target_currency].rate_per_unit

        if unit_to == 0:
            raise ZeroDivisionError(f"Rate for '{target_currency}' cannot be zero.")

        return amount * unit_from / unit_to

    def process_conversion_request(
        self,
        request: ConversionRequest,
        rates: Dict[str, ExchangeRate],
    ) -> ConversionResult:
        """Process a conversion request object [FR-004, FR-017]."""
        return request.process(rates)

    def get_pair_rate_display(
        self,
        source_currency: str,
        target_currency: str,
        rates: Dict[str, ExchangeRate],
    ) -> str:
        """Format pair rate as '1 <source> = X <target>' to 4 decimal places [FR-018]."""
        if source_currency == target_currency:
            return f"1 {source_currency} = 1.0000 {target_currency}"

        if source_currency not in rates or target_currency not in rates:
            return ""

        unit_from = rates[source_currency].rate_per_unit
        unit_to = rates[target_currency].rate_per_unit

        if unit_to == 0:
            return ""

        pair_rate = unit_from / unit_to
        return f"1 {source_currency} = {pair_rate:.4f} {target_currency}"

    def format_result(self, amount: float) -> str:
        """Format conversion result to two decimal places [FR-018]."""
        return f"{amount:.2f}"

    def get_rates_with_fallback(
        self,
        target_date: Optional[date] = None,
        use_cache: bool = True,
    ) -> Optional[RateResult]:
        """Retrieve rates for target_date.

        Falls back across 10 previous calendar days if empty [FR-014],
        or to local cache if network/source fails [FR-009, FR-010].
        """
        start_date = target_date or date.today()
        fetch_error: Optional[Exception] = None

        # Check today and up to 10 previous days (11 dates total)
        for days_back in range(11):
            check_date = start_date - timedelta(days=days_back)
            date_str = check_date.strftime("%d.%m.%Y")

            try:
                xml_content = self.fetch_xml_from_bnm(date_str)
            except Exception as e:
                fetch_error = e
                # Network failure stops live date iteration and tries cache fallback
                break

            try:
                # Check if response is empty
                if self.is_empty_response(xml_content):
                    continue

                rates, effective_date, source_name = self.parse_xml(xml_content)
                foreign_rates = {k: v for k, v in rates.items() if k != "MDL"}
                if not foreign_rates:
                    continue

                # Save successful rates to cache [FR-011, FR-019]
                self.cache_service.save_cache_if_valid(effective_date, source_name, rates)

                is_fallback = days_back > 0
                notice = (
                    f"Используется курс на {effective_date}."
                    if is_fallback
                    else ""
                )

                return RateResult(
                    rates=rates,
                    effective_date=effective_date,
                    source_name=source_name,
                    is_fallback=is_fallback,
                    notice=notice,
                )
            except ET.ParseError as pe:
                # Malformed XML is an error, not an empty response [FR-008]
                fetch_error = pe
                break

        # Fallback to local cache if available and permitted [FR-009, FR-010]
        if use_cache:
            cached_data = self.cache_service.load_cache()
            if cached_data:
                cached_rates: Dict[str, ExchangeRate] = {}
                eff_date = cached_data.get("effective_date", "")
                src_name = cached_data.get("source_name", "BNM")
                for code, info in cached_data.get("rates", {}).items():
                    cached_rates[code] = ExchangeRate(
                        currency_code=info["currency_code"],
                        rate_value=float(info["rate_value"]),
                        nominal=int(info.get("nominal", 1)),
                        effective_date=info.get("effective_date", eff_date),
                        source_name=info.get("source_name", src_name),
                        is_fallback=True,
                        currency_name=info.get("currency_name", ""),
                    )
                # Synthetic MDL
                cached_rates["MDL"] = ExchangeRate.create_mdl_rate(
                    effective_date=eff_date,
                    source_name=src_name,
                    currency_name="Молдавский лей",
                )

                if fetch_error is not None:
                    notice = f"Источник недоступен. Используется сохранённый курс на {eff_date} ({src_name})."
                else:
                    notice = f"Нет опубликованных курсов за последние 10 дней. Используется сохранённый курс на {eff_date} ({src_name})."

                return RateResult(
                    rates=cached_rates,
                    effective_date=eff_date,
                    source_name=src_name,
                    is_fallback=True,
                    notice=notice,
                )

        if fetch_error is not None:
            raise fetch_error

        return None
