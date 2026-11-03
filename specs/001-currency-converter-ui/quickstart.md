# Quickstart: Currency Converter UI

## Prerequisites

- Python 3.12+
- A local desktop environment with a graphical session
- Access to either the official BNM XML source or a fallback public API

## Setup

1. Create a virtual environment.
2. Install required dependencies for the chosen desktop stack.
3. Run the application entry point from the repository root.

## Validation scenarios

### 1. Successful conversion

- Enter a valid positive amount.
- Select different source and target currencies.
- Click the conversion button.
- Confirm the converted result appears together with the effective rate date and source.

### 2. Invalid input

- Enter `0`, a negative number, empty data, or letters.
- Confirm the conversion button remains disabled or the app shows a validation warning.
- Confirm no conversion executes.

### 3. Missing-rate fallback

- Select a date when no official rate is published.
- Confirm the app uses the latest available valid rate and displays a clear fallback notice.

### 4. Offline fallback

- Simulate network loss or failure.
- Confirm the app reuses the last successful cached response and informs the user.

### 5. Same-currency conversion

- Select the same currency in both fields.
- Confirm the app accepts the request and returns the original amount without error.

## Expected result

The feature is considered ready when all primary scenarios and edge cases pass without crashes, without silent data loss, and without undocumented fallback assumptions.
