# Implementation Plan: Currency Converter UI

**Branch**: `001-currency-converter-ui` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [spec.md](./spec.md)

## Summary

Build a small desktop currency conversion application that validates inputs, retrieves exchange rates from an authoritative source, falls back to the latest available rate when data is missing, and persists the last successful fetch locally so the user can continue without a network connection. The design emphasizes user clarity, deterministic conversion logic, and testable fallback behavior.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Tkinter for the GUI; Python standard library modules for XML parsing (`xml.etree.ElementTree`), HTTP requests (`urllib`/`requests`), and local persistence (`sqlite3` or JSON cache)

**Storage**: Local file-based cache for the most recent successful rate payload; optional SQLite database if structured history is needed for later audits

**Testing**: `pytest` for unit tests covering validation, fallback logic, and cache behavior; integration tests for source and offline scenarios

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
│   └── rate_cache.py
└── utils/
    ├── __init__.py
    └── currency_utils.py

tests/
├── unit/
│   ├── test_validation.py
│   ├── test_rate_fallback.py
│   └── test_cache.py
├── integration/
│   └── test_source_loading.py
└── fixtures/
    └── sample_bnm_response.xml
```

**Structure Decision**: Single desktop-app structure with a thin UI layer and explicit service modules for validation, rate retrieval, and local cache management. This keeps the application easy to test and aligns with the constitution’s maintainability and accuracy principles.

## Complexity Tracking

No constitution violations require additional justification for this feature. The scope stays within one small desktop application and the data flows remain straightforward.
