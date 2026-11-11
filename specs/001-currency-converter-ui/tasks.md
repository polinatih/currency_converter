# Tasks: Currency Converter UI

**Input**: Design documents from `/specs/001-currency-converter-ui/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, quickstart.md

**Organization**: Test tasks are completed before implementation tasks. Each implementation task identifies its prerequisite test task(s).

## Phase 1: Setup

**Purpose**: Create the application and test package structure.

- [X] T001 Create the package and test directory structure from `plan.md`, including `src/__init__.py`, `src/models/currency_pair.py`, `tests/__init__.py`, and `tests/fixtures/sample_bnm_response.xml`.

## Phase 2: Tests First

**Purpose**: Write the failing standard-library tests before implementing application behavior.

- [X] T002 [P] [US3] Write validation tests in `tests/test_validation.py` for empty, zero, negative, and non-numeric amounts, and for identical source and target currencies, asserting that a same-currency conversion is accepted and returns exactly the original amount [FR-003][FR-006][FR-007].
- [X] T003 [P] [US1] Write tests in `tests/test_rates.py` for BNM XML parsing, rate-per-nominal conversions USD-to-MDL, MDL-to-USD, USD-to-EUR, and EUR-to-USD, the pair-rate display `1 <source> = X <target>` to four decimal places, the conversion result to two decimal places, and `urllib` requests with a 10-second timeout [FR-004][FR-016][FR-017][FR-018][FR-020].
- [X] T004 [P] [US2] Write tests in `tests/test_rates.py` for empty responses, malformed XML, and date-by-date fallback through 10 previous days with a notice showing the effective date [FR-008][FR-014][FR-015].
- [X] T005 [P] [US2] Write tests in `tests/test_rates.py` for successful JSON cache persistence across restart, preservation when a response is empty or malformed, and malformed XML or network error with a valid cache causing cached rates to be used with their effective date shown [FR-009][FR-010][FR-011][FR-019].

## Phase 3: Foundational Implementation

**Purpose**: Implement shared domain and service foundations after the tests are defined.

- [X] T006 Create currency models in `src/models/conversion_request.py`, `src/models/exchange_rate.py`, `src/models/rate_cache.py`, and `src/models/currency_pair.py`, including BNM nominal values and the synthetic MDL rate [FR-004][FR-016][FR-017]. Depends on tests T002, T003, and T005.
- [X] T007 Implement BNM `urllib` fetching with a 10-second timeout, XML parsing, and normalization of each rate to MDL per one unit (`rate_value / nominal`, MDL = 1) in `src/services/rate_service.py`. This task does not apply rates to an amount and does not implement date-back or cache fallback [FR-013][FR-016][FR-017][FR-020]. Depends on test T003.
- [X] T008 Implement input validation in `src/services/validation_service.py` for empty, zero, negative, and non-numeric amounts and valid identical-currency requests [FR-003][FR-006][FR-007]. Depends on test T002.
- [X] T009 Implement persistence of the last successful parsed response in the single JSON cache file in `src/services/cache_service.py`; empty or malformed responses must not replace it [FR-011][FR-019]. Depends on test T005.
- [X] T010 Create the application entry point and window skeleton in `src/app.py` and `src/ui/main_window.py`, using the package structure from T001.

## Phase 4: User Story 1 - Convert money between currencies (Priority: P1)

**Goal**: Convert supported currencies in either direction and display the result, pair rate, date, and source.

**Independent Test**: Complete conversions between MDL/USD and USD/EUR in both directions and verify the formatted result and pair rate.

- [X] T011 [US1] Implement conversion request processing in `src/models/conversion_request.py` and `src/services/rate_service.py`: apply the per-unit rates normalized by T007 to the amount and currency pair (`amount * unit_from / unit_to`) and compute the pair rate [FR-004][FR-017]. Depends on test T003 and foundational tasks T006-T007.
- [X] T012 [P] [US1] Add source and target currency selectors in `src/ui/main_window.py` [FR-001][FR-002]. Depends on foundational task T010.
- [X] T013 [US1] Display the result to two decimal places and the pair rate as `1 <source> = X <target>` to four decimal places, together with the effective date and source, in `src/ui/main_window.py` [FR-005][FR-018]. Depends on test T003 and task T011.
- [X] T014 [US1] Connect the conversion button to validated calculation and display in `src/ui/main_window.py` [FR-003][FR-004][FR-005]. Depends on tests T002-T003 and tasks T008, T011, and T013.

## Phase 5: User Story 3 - Validate input (Priority: P1)

**Goal**: Reject invalid amounts and accept identical source and target currencies without error.

**Independent Test**: Exercise all invalid amount cases and same-currency conversion from the UI.

- [ ] T015 [US3] Prevent conversion when validation fails in `src/ui/main_window.py` [FR-003][FR-006]. Depends on test T002 and tasks T008 and T014.
- [ ] T016 [US3] Handle identical source and target currencies without error in `src/services/rate_service.py` and `src/ui/main_window.py` [FR-007]. Depends on test T002 and tasks T011 and T014.
- [ ] T017 [US3] Display clear validation feedback in `src/ui/main_window.py` [FR-006][FR-012]. Depends on test T002 and task T015.

## Phase 6: User Story 2 - Recover from missing or unavailable rates (Priority: P1)

**Goal**: Use the latest available rate with a date notice when today's rate is empty, and use cached rates when the source fails or no rate is found.

**Independent Test**: Verify date-by-date retries, and verify cached rate use and effective-date display after malformed XML or a network failure.

- [ ] T018 [US2] Implement date-back fallback in `src/services/rate_service.py`: after an empty response, request each previous day through 10 days before today and use the first valid rates [FR-008][FR-014][FR-015]. Depends on test T004 and task T007.
- [ ] T019 [US2] Implement fallback to the last successful cached response in `src/services/rate_service.py` when a network error or malformed XML occurs, or the 10-day search finds no rates [FR-009][FR-010][FR-019]. Depends on test T005 and tasks T007 and T009.
- [ ] T020 [US2] Display a clear error and prevent conversion when source retrieval fails, XML is malformed, or no rate is available and no cache can be used in `src/ui/main_window.py` [FR-009][FR-012]. Depends on tests T004-T005 and task T019.
- [ ] T021 [US2] Show an explicit latest-rate notice, effective date, and source in `src/ui/main_window.py` when an earlier or cached response is used [FR-005][FR-012][FR-015]. Depends on tests T004-T005 and tasks T018-T019.

## Phase 7: Polish and Cross-Cutting Concerns

- [ ] T022 [P] Run `py -m unittest` from the repository root and confirm all automated scenarios pass [SC-002][SC-003][SC-004][SC-005].
- [ ] T023 [P] Review and update `README.md` with the app purpose, usage, and fallback behavior [FR-008][FR-009][FR-012].
- [ ] T024 Document `py -m unittest` as the test command in `README.md` [FR-020].
- [ ] T025 Document `py -m src.app` as the launch command in `README.md` and align the instructions with `specs/001-currency-converter-ui/quickstart.md` (operational documentation task; no FR).
- [ ] T026 Run final automated regression with `py -m unittest`, then manually verify quickstart scenario 1 and SC-001's under-one-minute conversion target [SC-001][SC-002][SC-003][SC-004][SC-005].

## Dependencies and Execution Order

- Setup T001 precedes every other task.
- Tests First T002-T005 must be written before the foundational implementation tasks that they verify.
- Foundational tasks T006-T010 precede user-story implementation.
- User Story 1 tasks depend on conversion tests T003; User Story 3 tasks depend on validation test T002; User Story 2 tasks depend on fallback/cache tests T004-T005.
- User stories can proceed independently after the foundational phase, subject to their listed task dependencies. T018 and T019 are the only tasks implementing date-back and cached-rate fallback, respectively.

## Parallel Opportunities

- T002-T005 are independent test tasks and can be authored in parallel after T001.
- T006, T008, and T009 can proceed in parallel after the Tests First phase; T007 requires test T003.
- After foundations, T012 can proceed in parallel with service work not changing `src/ui/main_window.py`.

## Implementation Strategy

1. Create the package structure.
2. Write all unit tests before implementing the services they verify.
3. Implement the shared models and services.
4. Deliver the conversion flow, then validation and rate-recovery behavior.
5. Document run instructions, run `py -m unittest`, and manually check quickstart scenario 1 for SC-001.
