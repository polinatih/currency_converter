# Exchange Rate Source Contract

## Provider

The app uses an authoritative exchange-rate source, with BNM as the primary case study.

## Endpoint shape

- Source type: XML feed
- Example URL: `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`
- The feed is expected to return XML with normalized exchange-rate entries.

## Request semantics

- The request includes a target date.
- If the source does not publish data for that date, the app must treat the response as empty and select the latest valid cached or earlier rate.
- The app must not silently accept an empty or malformed response as a valid conversion basis.

## Response contract

The service should map source output into a normalized internal rate record containing:
- `source_name`
- `effective_date`
- `currency_code`
- `rate_value`
- `status` (`success`, `fallback`, `error`)

## Failure and fallback rules

- If the network request fails, the app must show a clear user message and prefer the local cache if available.
- If the provider returns no data for a selected date, the app must use the most recent valid rate and inform the user that the result is based on a fallback date.
- If the cache is empty and the source is unavailable, the app must show an explanatory error and prevent conversion.

## User-visible obligations

The app MUST always display:
- the conversion result,
- the effective rate date,
- the source that produced the rate.

This transparency is required to maintain trust and to support compliance with the project’s accuracy-first principle.
