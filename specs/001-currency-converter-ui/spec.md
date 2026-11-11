# Feature Specification: Currency Converter UI

**Feature Branch**: `001-currency-converter-ui`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Назначение. Конвертер валют с графическим интерфейсом. Источник данных: официальный XML-источник Национального банка Молдовы (BNM) является единственным источником курсов из-за его официального статуса и стабильной структуры. Справочно: BNM отдаёт данные в формате XML по адресу вида https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY. JSON-эндпоинта нет. Официальный курс публикуется в рабочие дни, обычно до 13:00 по времени Кишинёва, и действует весь следующий рабочий день. Интерфейс: поле ввода суммы, выбор исходной валюты, выбор целевой валюты, кнопка конвертации, неактивная до заполнения обязательных полей, отображение результата, отображение даты курса и источника данных. Обязательное поведение: Нет сети. Приложение не падает, выводит понятное сообщение, при наличии сохранённых данных предлагает работать с последним успешно полученным курсом с указанием его даты. Выходные и праздники. Если источник не публикует курс в выбранную дату, приложение корректно обрабатывает пустой ответ и берёт последний доступный курс, явно сообщая об этом пользователю. Некорректный ввод. Отрицательная сумма, ноль, буквы, пустое поле — приложение сообщает об ошибке и не выполняет конвертацию. Одинаковые валюты. Выбор одной и той же валюты в обоих списках обрабатывается без ошибки. Кэширование. Последний успешный ответ источника сохраняется локально и переживает перезапуск приложения."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert money between currencies (Priority: P1)

A user enters an amount and selects a source and target currency to obtain a conversion result quickly and clearly.

**Why this priority**: This is the core value of the feature and must work reliably for every supported use case.

**Independent Test**: A user can enter a valid amount, select currencies, submit the form, and receive the converted value along with the rate date and source.

**Acceptance Scenarios**:

1. **Given** the user has entered a positive amount and selected different currencies, **When** the conversion is requested, **Then** the system calculates the converted value and shows the result, rate date, and source.
2. **Given** the user has entered valid data but the rate source is temporarily unavailable, **When** the conversion is requested, **Then** the system does not crash and informs the user clearly whether it is using a cached rate.
3. **Given** the user converts between BNM-listed currencies or MDL, **When** the conversion is requested, **Then** the amount is converted using each currency's rate per nominal unit, including a rate of 1 and nominal of 1 for MDL.
4. **Given** the user converts USD to EUR or EUR to USD, **When** the conversion is requested, **Then** the result is correct in both directions using the rates relative to MDL.
5. **Given** the app displays a conversion, **When** the result and rate are shown, **Then** the result has two decimal places and the rate has four decimal places.

---

### User Story 2 - Recover from missing or outdated rates (Priority: P1)

A user should be able to continue working even when the rate source is absent, a holiday excludes the current date, or the network is unavailable.

**Why this priority**: The feature must remain usable in real-world conditions where exchange rates are not published every day or the connection is not available.

**Independent Test**: The user can trigger a conversion during an offline or missing-rate condition and see the system select the latest available rate with a clear explanation.

**Acceptance Scenarios**:

1. **Given** today has no published rate, **When** the conversion is requested, **Then** the system requests each previous calendar day in turn, up to 10 days before today, and uses the first available rate with a notice showing its effective date.
2. **Given** no network is available and a previous successful rate is cached locally, **When** the conversion is requested, **Then** the system automatically uses the last successful cached rate and shows a clear notice that the network is unavailable, together with the cached rate's effective date and source.
3. **Given** no rate is found today or in the 10 preceding days, **When** a valid cached response is available, **Then** the system uses it and clearly identifies its effective date.

---

### User Story 3 - Validate user input and prevent invalid conversions (Priority: P1)

A user must receive actionable feedback for invalid amounts and invalid currency selections before the conversion is executed.

**Why this priority**: Invalid input is one of the most common sources of incorrect financial results, and the application must protect users from unintended actions.

**Independent Test**: Users can test empty, negative, zero, or non-numeric values and see blocked conversions with clear errors.

**Acceptance Scenarios**:

1. **Given** the amount field is empty, negative, zero, or contains letters, **When** the user attempts to convert, **Then** the system rejects the request and displays a clear validation message.
2. **Given** the user selects the same currency in both fields, **When** the conversion request is sent, **Then** the system handles the scenario without an error and returns the same value with the effective rate date and source information.

---

### Edge Cases

- What happens when today's response is empty on a weekend or holiday?
- How does the system behave when the source returns an empty response or the request fails without a network connection?
- What happens when the user changes the source and target currencies after a previous successful conversion?
- How does the system handle cached data after the application restarts?
- How does the system handle malformed XML or a search with no rate within the 10-day window?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an input field for the amount to convert.
- **FR-002**: The system MUST allow the user to select both a source currency and a target currency.
- **FR-003**: The conversion button MUST remain disabled until the required fields are populated and the input is valid.
- **FR-004**: The system MUST calculate the converted value when a valid request is submitted.
- **FR-005**: The system MUST display the converted result together with the effective exchange rate date and the source used for the calculation.
- **FR-006**: The system MUST reject empty, zero, negative, or non-numeric amount values with a clear validation message and without executing the conversion.
- **FR-007**: The system MUST handle identical source and target currencies as a valid scenario and must not fail or block the conversion.
- **FR-008**: The system MUST treat missing or empty rate responses as a data availability issue and use the most recent available rate when one exists, while clearly informing the user.
- **FR-009**: The system MUST continue to function without network access and must not crash when the exchange rate source is unavailable.
- **FR-010**: When the source is unavailable, the system MUST automatically reuse the last successfully retrieved rate when available (no confirmation dialog), including after application restart, and MUST show a notice explaining that a cached rate is being used together with its effective date.
- **FR-011**: The system MUST persist the most recent successful source response locally so it remains available across application restarts.
- **FR-012**: The system MUST present user-facing messages that clearly explain validation failures, network issues, fallback behavior, and missing-rate situations.
- **FR-013**: The system MUST use the official BNM XML feed as its exchange-rate source and display BNM as the source for rates retrieved from it.
- **FR-014**: The system MUST request rates for today's date without offering a date picker. If the valid response contains no rates, it MUST request the previous calendar date one day at a time, checking through the date 10 days before today.
- **FR-015**: When a rate from an earlier date is used, the system MUST show a notice that the latest available rate is being used and identify that rate's effective date.
- **FR-016**: The system MUST interpret each BNM rate as MDL per `Nominal` units of the quoted currency, and MUST treat MDL as rate 1 with nominal 1 even though MDL is absent from the feed.
- **FR-017**: The system MUST calculate conversions in either direction using `amount * (rate_from / nominal_from) / (rate_to / nominal_to)`, including conversions to and from MDL and between two non-MDL currencies.
- **FR-018**: The system MUST display the conversion result with two decimal places and the selected currency-pair rate as `1 <source> = X <target>` with four decimal places, where `X = (rate_from / nominal_from) / (rate_to / nominal_to)`.
- **FR-019**: The system MUST save the last successful parsed response in a single local JSON cache file containing its effective date, source, and rates. Empty, malformed, or failed responses MUST NOT replace that cache.
- **FR-020**: The system MUST use only the Python standard library, retrieve the XML feed with `urllib`, and apply a 10-second network timeout.

**Canonical Fallback Policy**: Request today's BNM XML rates first. When a well-formed response has no rates, retry the previous calendar day one day at a time, through 10 days before today, and use the first available response. When an earlier date is used, show a notice identifying its effective date. If the source cannot be reached, returns malformed data, or has no available rates in that window, use the last successful cached response if one exists and identify its date and source; otherwise show a clear error and do not convert. Never replace a successful cache with empty, malformed, or failed data.

### Key Entities

- **ConversionRequest**: Represents the user-entered amount, source currency, target currency, and requested conversion context.
- **ExchangeRate**: Represents a published currency rate together with its effective date and data source.
- **RateCache**: Represents the locally stored most recent successful source response and its metadata, retained for reuse after restart.
- **CurrencyPair**: Represents the relationship between the selected source and target currencies used for the conversion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a valid conversion in under 1 minute without needing technical guidance.
- **SC-002**: Invalid inputs are rejected consistently and do not trigger a conversion in 100% of validation cases.
- **SC-003**: The application continues to operate during missing-network or missing-rate conditions and clearly informs the user when fallback data is being used.
- **SC-004**: The most recent successful rate remains available after restart and can be used without re-fetching the source.
- **SC-005**: The displayed result includes the effective rate date and source, so the user can verify the basis of the converted amount.

## Assumptions

- Users expect a simple, reliable conversion interface that works even when the network or source data is inconsistent.
- The official BNM XML feed is the only exchange-rate source in scope.
- BNM rates represent MDL per `Nominal` units; MDL is absent from the feed and is represented as rate 1, nominal 1.
- Official BNM data is published only on working days, so fallback logic is required for holidays, weekends, and missing publication periods.
- The application stores one last-successful parsed response in a local JSON file to support recovery after restart.
- The app requests today's date automatically; the user does not select a rate date.
- The app uses only the Python standard library, with `urllib` and a 10-second request timeout.
