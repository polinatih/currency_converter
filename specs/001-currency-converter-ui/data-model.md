# Data Model: Currency Converter UI

## Core entities

### ConversionRequest

Represents the user’s request to convert one amount from a source currency to a target currency.

**Fields**:
- `amount`: positive decimal value entered by the user
- `source_currency`: code such as USD or EUR
- `target_currency`: code such as MDL or USD

**Validation rules**:
- Amount MUST be a positive number greater than zero.
- Amount MUST not be empty, negative, zero, or contain non-numeric characters.
- Source and target currency may be identical; in that case the conversion result is the same amount and no error is raised.
- The app requests rates for today's date; the user does not choose a rate date.

### ExchangeRate

Represents a single currency rate published by the source along with its source metadata.

**Fields**:
- `source_name`: authoritative provider name such as BNM
- `effective_date`: date on which the rate is valid
- `target_currency`: quoted currency code
- `rate_value`: numeric MDL value quoted by BNM for the nominal quantity
- `nominal`: number of units of `target_currency` represented by `rate_value`
- `is_fallback`: whether the value was chosen as a fallback because the exact date was unavailable

**Validation rules**:
- Rate values MUST be numeric and positive.
- `nominal` MUST be numeric and positive.
- BNM's `rate_value / nominal` is the MDL value of one unit of the quoted currency.
- MDL is not present in the BNM feed and MUST be represented as rate 1, nominal 1.
- The source and date MUST be retained in the UI for user transparency.
- Fallback usage MUST be explicit to the user and not silent.

### RateCache

Represents the last successful source response saved locally after a valid fetch.

**Fields**:
- `effective_date`: date of the last successful parsed response
- `source_name`: provider name for that response
- `rates`: parsed rates, each with currency code, rate value, and nominal

The cache is one local JSON file containing the effective date, source, and rates.

**Validation rules**:
- The cache MUST contain only the last successful parsed response.
- Empty, malformed, or failed responses MUST NOT replace a previously valid cache entry.
- Cached rates MUST retain the response's effective date and source.

### CurrencyPair

Represents the chosen directional conversion pair used in the calculation.

**Fields**:
- `source_currency`
- `target_currency`
- `rate_from`: effective rate record for the source currency
- `rate_to`: effective rate record for the target currency
- `pair_rate`: target-currency units per one source-currency unit

**Relationships**:
- A `CurrencyPair` references both `ExchangeRate` records used to perform the conversion.
- A `ConversionRequest` produces exactly one `CurrencyPair` for the requested conversion operation.
- A `RateCache` can supply the `ExchangeRate` used when the network or exact-date source is unavailable.

**Derived value**:
- `pair_rate = (rate_from.rate_value / rate_from.nominal) / (rate_to.rate_value / rate_to.nominal)`.
- Display the pair rate as `1 <source_currency> = <pair_rate> <target_currency>` with four decimal places.

## State transitions

- `Idle`: user has not yet entered a valid conversion request.
- `Validating`: application checks input and required fields.
- `LoadingRate`: app requests today's rate and may check previous dates if a valid response is empty.
- `FallbackRateUsed`: an earlier date or cached response is used with a user-visible notice and its effective date.
- `Completed`: converted value is displayed with rate date and source metadata.
- `Error`: invalid input or missing rate data prevented conversion.

## Derived logic

- For a BNM-listed currency, `rate_value / nominal` is its MDL value per one currency unit. For MDL, the rate and nominal are both 1.
- The conversion result is `amount * (rate_from / nominal_from) / (rate_to / nominal_to)`. This supports both conversion directions and conversions between two non-MDL currencies.
- The app requests today's rates first. If a well-formed response has no rates, it requests each previous calendar day in turn, through 10 days before today, and uses the first available response.
- The app displays the result with two decimal places and the currency-pair rate (`1 <source> = X <target>`) with four decimal places.
- If the source is unavailable, the response is malformed, or no rates are found within the date search, the application MUST use the last successful cached response if available and display its effective date and source; otherwise it MUST report an error.
