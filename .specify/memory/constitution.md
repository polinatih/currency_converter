<!--
Sync Impact Report:
- Version change: unversioned → 1.0.0
- Modified principles: Principle 1 → Accuracy First; Principle 2 → User-Centered Interface; Principle 3 → Test-First Validation; Principle 4 → Security & Data Integrity; Principle 5 → Maintainability & Simplicity
- Added sections: Operational Constraints; Development Workflow
- Removed sections: None
- Follow-up TODOs: TODO(RATIFICATION_DATE): Original adoption date is not yet recorded.
-->

# Currency Converter Constitution

## Core Principles

### I. Accuracy First
Currency conversion results MUST be based on explicit, documented rate sources and deterministic calculation rules. Any rounding, fallback strategy, or assumption about source data must be stated clearly and reflected in tests before release.

### II. User-Centered Interface
The converter MUST present values, currencies, and results in a way that is readable, unambiguous, and easy to validate. Hidden defaults, unclear labels, and ambiguous input rules are prohibited because they create incorrect user outcomes.

### III. Test-First Validation
Every supported currency pair, conversion edge case, and validation rule MUST have automated tests before the code is considered complete. Any bug fix or behavior change MUST include a failing test when the issue is reproducible.

### IV. Security & Data Integrity
Inputs and external data MUST be validated, sanitized, and handled safely. The project MUST reject malformed values, prevent silent corruption from stale or untrusted data, and fail clearly when a dependency or source cannot provide trustworthy results.

### V. Maintainability & Simplicity
The codebase MUST favor clear, small, testable units over clever abstractions. Changes must preserve or improve readability, avoid unnecessary dependencies, and document any intentional behavior that is not self-evident.

## Operational Constraints

The project is a focused currency conversion tool and MUST remain easy to understand, run, and validate. Configuration, rate sources, and conversion assumptions MUST be explicit and discoverable in the repository so contributors can verify behavior without reverse engineering the implementation.

The project MUST avoid hard-coded secrets, undocumented external dependencies, and silent changes in business rules. When conversion logic or supported currencies change, the documentation and tests MUST change in the same review.

## Development Workflow

All changes MUST be reviewed for correctness, clarity, and compliance with this constitution before merge. Each contribution MUST include or update tests that validate the intended behavior, and any change to calculation logic or user-facing output MUST be accompanied by clear notes in the repository documentation.

The project MUST keep the default path to correctness simple: implement the smallest change, validate it with automated checks, and verify that the behavior matches the documented conversion rules. Releases must not ship with untested assumptions about rates, rounding, or error handling.

## Governance

This constitution governs all project decisions that affect behavior, quality, and operational safety. Any amendment MUST be documented, reviewed, and linked to the specific change it is modifying so contributors can trace the reasoning behind the rule.

All changes must be checked against this document before merge. If a rule is unclear, the team MUST resolve the ambiguity before proceeding rather than relying on informal exceptions. When a project decision conflicts with this constitution, the constitution takes precedence unless a formal amendment is adopted.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Original adoption date is not yet recorded. | **Last Amended**: 2026-11-04
