# Feature Specification: Currency Converter UI

**Feature Branch**: `001-currency-converter-ui`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Назначение. Конвертер валют с графическим интерфейсом. Источник данных: официальный XML-источник Национального банка Молдовы (BNM) является основным и предпочтительным вариантом из-за его официального статуса и стабильной структуры; альтернативный бесплатный API допустим только как явно задокументированная замена при эквивалентном поведении. Справочно: BNM отдаёт данные в формате XML по адресу вида https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY. JSON-эндпоинта нет. Официальный курс публикуется в рабочие дни, обычно до 13:00 по времени Кишинёва, и действует весь следующий рабочий день. Интерфейс: поле ввода суммы, выбор исходной валюты, выбор целевой валюты, кнопка конвертации, неактивная до заполнения обязательных полей, отображение результата, отображение даты курса и источника данных. Обязательное поведение: Нет сети. Приложение не падает, выводит понятное сообщение, при наличии сохранённых данных предлагает работать с последним успешно полученным курсом с указанием его даты. Выходные и праздники. Если источник не публикует курс в выбранную дату, приложение корректно обрабатывает пустой ответ и берёт последний доступный курс, явно сообщая об этом пользователю. Некорректный ввод. Отрицательная сумма, ноль, буквы, пустое поле — приложение сообщает об ошибке и не выполняет конвертацию. Одинаковые валюты. Выбор одной и той же валюты в обоих списках обрабатывается без ошибки. Кэширование. Последний успешный ответ источника сохраняется локально и переживает перезапуск приложения."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert money between currencies (Priority: P1)

A user enters an amount and selects a source and target currency to obtain a conversion result quickly and clearly.

**Why this priority**: This is the core value of the feature and must work reliably for every supported use case.

**Independent Test**: A user can enter a valid amount, select currencies, submit the form, and receive the converted value along with the rate date and source.

**Acceptance Scenarios**:

1. **Given** the user has entered a positive amount and selected different currencies, **When** the conversion is requested, **Then** the system calculates the converted value and shows the result, rate date, and source.
2. **Given** the user has entered valid data but the rate source is temporarily unavailable, **When** the conversion is requested, **Then** the system does not crash and informs the user clearly whether it is using a cached rate.

---

### User Story 2 - Recover from missing or outdated rates (Priority: P1)

A user should be able to continue working even when the rate source is absent, a holiday excludes the current date, or the network is unavailable.

**Why this priority**: The feature must remain usable in real-world conditions where exchange rates are not published every day or the connection is not available.

**Independent Test**: The user can trigger a conversion during an offline or missing-rate condition and see the system select the latest available rate with a clear explanation.

**Acceptance Scenarios**:

1. **Given** the selected date has no published rate and a more recent available rate exists, **When** the conversion is requested, **Then** the system uses the latest available rate and clearly states that it is a fallback result.
2. **Given** no network is available and a previous successful rate is cached locally, **When** the conversion is requested, **Then** the system offers or uses the last successful rate and shows the relevant date.

---

### User Story 3 - Validate user input and prevent invalid conversions (Priority: P1)

A user must receive actionable feedback for invalid amounts and invalid currency selections before the conversion is executed.

**Why this priority**: Invalid input is one of the most common sources of incorrect financial results, and the application must protect users from unintended actions.

**Independent Test**: Users can test empty, negative, zero, or non-numeric values and see blocked conversions with clear errors.

**Acceptance Scenarios**:

1. **Given** the amount field is empty, negative, zero, or contains letters, **When** the user attempts to convert, **Then** the system rejects the request and displays a clear validation message.
2. **Given** the user selects the same currency in both fields, **When** the conversion request is sent, **Then** the system handles the scenario without an error and returns the same value with the selected date and source information.

---

### Edge Cases

- What happens when the user submits a conversion on a weekend or holiday when no rate is published?
- How does the system behave when the source returns an empty response or the request fails without a network connection?
- What happens when the user changes the source and target currencies after a previous successful conversion?
- How does the system handle cached data after the application restarts?

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
- **FR-010**: The system MUST offer or reuse the last successfully retrieved rate when available, including after application restart, and must display the corresponding date.
- **FR-011**: The system MUST persist the most recent successful source response locally so it remains available across application restarts.
- **FR-012**: The system MUST present user-facing messages that clearly explain validation failures, network issues, fallback behavior, and missing-rate situations.
- **FR-013**: The system MUST use the official BNM XML feed as the default source. An alternative free public exchange-rate API is allowed only when it is explicitly documented, provides equivalent behavior, and still displays the source and effective date to the user.

**Canonical Fallback Policy**: When the selected date has no published rate or the source is unavailable, the system MUST use the latest valid cached or previously successful rate, clearly label the value as a fallback, and show the corresponding rate date and source. This rule is the single source of truth for offline, holiday, and missing-rate behavior.

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
- The official BNM XML feed is the default source for the project, and any alternative public exchange-rate API must be documented and validated as an explicit substitute.
- Official BNM data is published only on working days, so fallback logic is required for holidays, weekends, and missing publication periods.
- The application is expected to store the last successful rate locally on the device to support recovery after restart.
- The source may not always be available at the exact time the user requests a conversion, so the system must handle stale or missing data gracefully.
