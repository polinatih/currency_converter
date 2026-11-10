# Implementation Plan: Currency Converter UI

**Branch**: `001-currency-converter-ui` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [spec.md](./spec.md)

## Summary

Build a small desktop currency conversion application that validates inputs, retrieves BNM exchange rates, falls back to earlier dates or the last successful cached response when data is missing, and persists that response locally so the user can continue without a network connection. The design emphasizes user clarity, correct per-nominal conversion logic, and testable fallback behavior.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Tkinter and Python standard library modules only, including `xml.etree.ElementTree`, `urllib`, and JSON file handling. Network requests use a 10-second timeout. No third-party dependencies.

**Application Launch**: Run `py -m src.app` from the repository root. All application imports use absolute package paths rooted at the repository, for example `from src.services.rate_service import ...`.

**Source Policy**: The official BNM XML feed is the only exchange-rate source. Its rates are MDL per `Nominal` units of each currency; MDL is not listed and is represented internally as rate 1, nominal 1. A well-formed response with no rates triggers requests for the previous calendar day one day at a time, through 10 days before today. An earlier effective date is shown in a user-visible notice. The displayed pair rate is `1 <source> = X <target>`, where `X = (rate_from / nominal_from) / (rate_to / nominal_to)`.

**Storage**: One local JSON cache file containing the last successful parsed response's effective date, source, and rates. Empty, malformed, or failed responses never replace it.

**Testing**: Python standard library `unittest` only. Run all tests from the repository root with `py -m unittest`. `tests/test_rates.py` covers BNM XML parsing, rate-per-nominal conversion in both directions, empty and malformed responses, fallback, and cache behavior. `tests/test_validation.py` covers input validation and same-currency handling.

**Target Platform**: Desktop, cross-platform Windows/macOS/Linux support with a single GUI application

**Project Type**: desktop-app

**Performance Goals**: Conversion request response should be effectively instant for local calculations, with source fetches and fallback decisions completing within a few seconds under normal conditions

**Constraints**: Must work without network access by using cached data; must handle missing published rates on weekends/holidays; must display a clear explanation for fallback and validation issues

**Scale/Scope**: Single user, small-to-medium data set, limited to currency conversion and rate caching workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accuracy First: PASS — The feature requires explicit rate sources, fallback transparency, and date-aware behavior.
- User-Centered Interface: PASS — The app must validate inputs, explain state clearly, and show source/date metadata.
- Test-First Validation: PASS — Every conversion rule and fallback path is expected to have automated coverage before completion.
- Security & Data Integrity: PASS — Input validation, rate-source checks, and local cache integrity are required.
- Maintainability & Simplicity: PASS — The design keeps the scope limited to a single desktop app with clear service boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/001-currency-converter-ui/
├── plan.md              # This file
├── research.md          # Design decisions and vendor/source analysis
├── data-model.md        # Domain entities and validation rules
├── quickstart.md        # Validation run guide
├── contracts/           # Source and fallback contracts
└── tasks.md             # Generated in the next phase, not created here
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── app.py
├── ui/
│   ├── __init__.py
│   └── main_window.py
├── services/
│   ├── __init__.py
│   ├── rate_service.py
│   ├── cache_service.py
│   └── validation_service.py
├── models/
│   ├── __init__.py
│   ├── conversion_request.py
│   ├── exchange_rate.py
│   ├── rate_cache.py
│   └── currency_pair.py
└── utils/
    ├── __init__.py
    └── currency_utils.py

tests/
├── __init__.py
├── test_rates.py
├── test_validation.py
└── fixtures/
    └── sample_bnm_response.xml
```

**Structure Decision**: Single desktop-app structure with `src` as a Python package, a thin UI layer, and explicit service modules for validation, rate retrieval, and local cache management. Imports use absolute paths rooted at the repository, and the app is launched with `py -m src.app`. The `tests` package and consistently named standard-library test modules support discovery with `py -m unittest` from the repository root.

## Complexity Tracking

No constitution violations require additional justification for this feature. The scope stays within one small desktop application and the data flows remain straightforward.
