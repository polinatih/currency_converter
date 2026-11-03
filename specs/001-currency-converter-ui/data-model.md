# Data Model: Currency Converter UI

## Core entities

### ConversionRequest

Represents the user’s request to convert one amount from a source currency to a target currency.

**Fields**:
- `amount`: positive decimal value entered by the user
- `source_currency`: code such as USD or EUR
- `target_currency`: code such as MDL or USD
- `requested_date`: date the user expects to evaluate, if applicable

**Validation rules**:
- Amount MUST be a positive number greater than zero.
- Amount MUST not be empty, negative, zero, or contain non-numeric characters.
- Source and target currency may be identical; in that case the conversion result is the same amount and no error is raised.

### ExchangeRate

Represents a single currency rate published by the source along with its source metadata.

**Fields**:
- `source_name`: authoritative provider name such as BNM
- `effective_date`: date on which the rate is valid
- `base_currency`: reference currency used by the provider
- `target_currency`: quoted currency code
- `rate_value`: numeric conversion factor or rate
- `is_fallback`: whether the value was chosen as a fallback because the exact date was unavailable

**Validation rules**:
- Rate values MUST be numeric and positive.
- The source and date MUST be retained in the UI for user transparency.
- Fallback usage MUST be explicit to the user and not silent.

### RateCache

Represents the last successful source response saved locally after a valid fetch.

**Fields**:
- `cached_at`: timestamp when the response was last saved
- `source_name`: provider name
- `effective_date`: date of the saved rate
- `payload`: raw or normalized rate payload used for later retrieval
- `status`: last operation result (`success`, `empty`, `error`)

**Validation rules**:
- Cache entries MUST be read-only until replaced by a newer successful fetch.
- Empty or failed responses MUST not overwrite a previously valid cache entry without a clear rule.

### CurrencyPair

Represents the chosen directional conversion pair used in the calculation.

**Fields**:
- `source_currency`
- `target_currency`
- `rate_reference`: the effective exchange rate record used for the calculation

**Relationships**:
- A `CurrencyPair` references one `ExchangeRate` record used to perform the conversion.
- A `ConversionRequest` produces exactly one `CurrencyPair` for the requested conversion operation.
- A `RateCache` can supply the `ExchangeRate` used when the network or exact-date source is unavailable.

## State transitions

- `Idle`: user has not yet entered a valid conversion request.
- `Validating`: application checks input and required fields.
- `LoadingRate`: app attempts to fetch or read the active rate.
- `FallbackRateUsed`: no exact-date value exists; latest valid cached or prior rate is used with a user-visible notice.
- `Completed`: converted value is displayed with rate date and source metadata.
- `Error`: invalid input or missing rate data prevented conversion.

## Derived logic

- The conversion result is calculated as `amount * rate_value` using the selected source and target rate pair.
- If the selected date does not have a published rate, the application MUST pick the most recent available rate and indicate that the value is a fallback.
- If the network is down and cache is available, the application MUST prefer the last successful cached rate and display the date from that cached entry.
