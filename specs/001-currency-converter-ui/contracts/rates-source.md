# Exchange Rate Source Contract

## Provider

The app uses the official National Bank of Moldova (BNM) XML exchange-rate feed:

`https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`

Only Python standard-library components are used. Requests use `urllib` with a 10-second timeout.

## Request semantics

- The app requests today's date automatically; the UI has no date picker.
- A well-formed response containing no rate entries is an empty response. After an empty response, request the previous calendar date, one day at a time, checking through 10 days before today (up to 11 dates including today).
- Use the first date with a non-empty, valid response. If it is earlier than today, show a notice that the latest available rate is being used and include its effective date.
- Malformed XML is an error, not an empty response; do not treat it as a reason to continue the date search or as a valid rate.
- If the date search finds no rates, or a request fails or returns malformed XML, use the last successful cached response if available. If no cache is available, show an error and prevent conversion.

## Response contract

Each BNM XML entry describes a currency rate in MDL for a `Nominal` quantity of the quoted currency. Parse each entry into:

- `source_name`: `BNM`
- `effective_date`: the date represented by the response
- `currency_code`: the quoted currency code
- `rate_value`: the MDL amount quoted by BNM
- `nominal`: the quoted number of currency units

The rate per one unit is `rate_value / nominal`. Because MDL is not included in the feed, add an internal MDL rate with `rate_value = 1` and `nominal = 1`.

## Conversion

For source and target rates represented by `(rate_from, nominal_from)` and `(rate_to, nominal_to)`, calculate:

`result = amount * (rate_from / nominal_from) / (rate_to / nominal_to)`

This formula applies in either direction, including conversions to or from MDL and conversions between two non-MDL currencies.

Display the selected pair rate as `1 <source_currency> = X <target_currency>`, where `X = (rate_from / nominal_from) / (rate_to / nominal_to)`, with four decimal places. Display the converted result with two decimal places.

## Cache contract

Maintain a single local JSON file containing the last successfully parsed response: its effective date, source, and rates (currency code, rate value, and nominal). A successful response may replace this file. Empty, malformed, and failed responses must never overwrite it.

## User-visible obligations

The app MUST display the conversion result, effective rate date, and source. When an earlier date or cached response is used, it MUST explain that the latest available rate is being used and identify that rate's date.
