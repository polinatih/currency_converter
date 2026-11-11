# Quickstart: Currency Converter UI

## Prerequisites

- Python 3.12+
- A local desktop environment with a graphical session
- No third-party dependencies

## Setup and run

From the repository root, launch the application with:

```powershell
py -m src.app
```

Run the standard-library test suite from the repository root with:

```powershell
py -m unittest
```

## Validation scenarios

### 1. Successful conversion

- Enter a valid positive amount.
- Select different source and target currencies.
- Click the conversion button.
- Confirm the converted result appears together with the effective rate date and source.
- Manually verify that a valid conversion can be completed in under one minute without technical guidance (SC-001).

### 2. Invalid input

- Enter `0`, a negative number, empty data, or letters.
- Confirm the conversion button remains disabled or the app shows a validation warning.
- Confirm no conversion executes.

### 3. Missing-rate fallback

- Start with today's rate request; do not select a date.
- When today's response is empty, as on a weekend or holiday, confirm the app requests each previous day in turn, up to 10 days before today.
- Confirm it uses the first available rate and shows a notice with that rate's effective date.

### 4. Malformed XML

- Provide a malformed XML response.
- Confirm the app reports the response error and does not treat it as an empty or valid rate response.
- If a successful cache exists, confirm the app uses it and identifies its effective date.

### 5. Offline fallback and cache persistence

- Successfully retrieve rates and close the app.
- Confirm the last successful parsed response remains available after restarting the app.
- Simulate network loss and confirm the app reuses the cached rates and informs the user.

### 6. Conversion directions

- Convert MDL to USD and USD to MDL; confirm both directions return the expected results.
- Convert USD to EUR and EUR to USD; confirm both directions return the expected results.

### 7. Same-currency conversion

- Select the same currency in both fields.
- Confirm the app accepts the request and returns the original amount without error.

## Expected result

The feature is considered ready when all primary scenarios and edge cases pass without crashes, without silent data loss, and without undocumented fallback assumptions.
