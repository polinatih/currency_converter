# Tasks: Currency Converter UI

**Input**: Design documents from `/specs/001-currency-converter-ui/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and core desktop app structure

- [ ] T001 Create project structure per implementation plan in `src/`, `src/ui/`, `src/services/`, `src/models/`, and `tests/`
- [ ] T002 Initialize Python 3.12 project dependencies and runtime setup in `requirements.txt` and `src/app.py`
- [ ] T003 [P] Configure project testing and formatting in `pytest.ini` and `requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core application infrastructure that MUST be complete before user story work begins

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

- [ ] T004 Create currency models in `src/models/conversion_request.py`, `src/models/exchange_rate.py`, `src/models/rate_cache.py`, and `src/models/currency_pair.py`
- [ ] T005 [P] Implement validation service in `src/services/validation_service.py` with rules for empty, zero, negative, and non-numeric amounts
- [ ] T006 [P] Implement local cache service in `src/services/cache_service.py` for persisted last-successful-rate storage
- [ ] T007 [P] Implement rate source service in `src/services/rate_service.py` for XML fetch, conversion, and fallback logic
- [ ] T008 Create desktop application entry point and window skeleton in `src/app.py` and `src/ui/main_window.py`
- [ ] T009 Set up user-visible error handling and status messaging in `src/ui/main_window.py`

---

## Phase 3: User Story 1 - Convert money between currencies (Priority: P1) 🎯 MVP

**Goal**: Allow a user to enter an amount, select currencies, and receiving a valid converted result with the rate date and source metadata.

**Independent Test**: A user can complete a valid conversion request using different source and target currencies and confirm the result is displayed together with the source and date.

### Tests for User Story 1

- [ ] T010 [P] [US1] Write failing conversion tests in `tests/unit/test_conversion.py` for valid input and result formatting
- [ ] T011 [P] [US1] Write integration test in `tests/integration/test_conversion_flow.py` for the full successful conversion path

### Implementation for User Story 1

- [ ] T012 [US1] Implement conversion request processing in `src/models/conversion_request.py` and `src/services/rate_service.py`
- [ ] T013 [US1] Implement the conversion result view and button behavior in `src/ui/main_window.py`
- [ ] T014 [P] [US1] Add source and target currency selectors in `src/ui/main_window.py`
- [ ] T015 [US1] Add result, rate date, and source metadata display in `src/ui/main_window.py`
- [ ] T016 [US1] Connect the conversion button to validation and calculation flow in `src/ui/main_window.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Recover from missing or outdated rates (Priority: P1)

**Goal**: Ensure the app remains usable when the source is unavailable, the selected date has no published rate, or the network is offline.

**Independent Test**: A user can trigger a conversion under a missing-rate or offline condition and confirm the app uses the last valid rate with a clear fallback message.

### Tests for User Story 2

- [ ] T017 [P] [US2] Write failing offline and fallback tests in `tests/unit/test_rate_fallback.py`
- [ ] T018 [P] [US2] Write integration test in `tests/integration/test_fallback_flow.py` for cached-rate recovery after source failure

### Implementation for User Story 2

- [ ] T019 [US2] Implement fallback selection logic in `src/services/rate_service.py` to use the latest available valid rate when the date has no publishable result
- [ ] T020 [US2] Implement offline reuse and persistence in `src/services/cache_service.py` for the locally stored last successful response
- [ ] T021 [US2] Add explicit fallback messaging in `src/ui/main_window.py` and `src/services/rate_service.py`
- [ ] T022 [US2] Ensure the effective fallback date is shown together with the source in `src/ui/main_window.py`

**Checkpoint**: At this point, User Story 2 should operate correctly without a crashing or silent failure path.

---

## Phase 5: User Story 3 - Validate input and prevent invalid conversions (Priority: P1)

**Goal**: Reject invalid values early and provide clear user feedback without executing conversions with broken input.

**Independent Test**: A user can submit empty, zero, negative, or non-numeric amounts, and the system blocks conversion while showing a clear validation error.

### Tests for User Story 3

- [ ] T023 [P] [US3] Write failing validation tests in `tests/unit/test_validation.py` for empty, zero, negative, and letter input
- [ ] T024 [P] [US3] Add same-currency scenario test in `tests/unit/test_validation.py` to confirm no error on identical source and target selections

### Implementation for User Story 3

- [ ] T025 [US3] Enforce validation rules in `src/services/validation_service.py` for the required amount and currency conditions
- [ ] T026 [US3] Prevent conversion execution when validation fails in `src/ui/main_window.py`
- [ ] T027 [US3] Handle same-currency selections without error in `src/services/rate_service.py` and `src/ui/main_window.py`
- [ ] T028 [US3] Add user-friendly validation and warning messages in `src/ui/main_window.py`

**Checkpoint**: At this point, all primary conversion flows and edge cases are independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, cleanup, and multi-story quality checks

- [ ] T029 [P] Run the complete validation flow from `specs/001-currency-converter-ui/quickstart.md` and confirm all key scenarios pass
- [ ] T030 [P] Review and update `README.md` with the app purpose, usage, and fallback behavior
- [ ] T031 Clean up repeated logic and ensure consistent naming and messaging across `src/ui/main_window.py`, `src/services/rate_service.py`, and `src/services/cache_service.py`
- [ ] T032 Final regression run across `tests/unit/` and `tests/integration/` to confirm the feature is stable and user-safe

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Story Phases (Phase 3-5)**: Depend on Foundational completion and can be implemented in parallel if multiple contributors are available
- **Polish (Phase 6)**: Depends on all desired user stories being complete and validated

### User Story Dependencies

- **User Story 1 (US1)**: Can start after Phase 2 and is the core MVP
- **User Story 2 (US2)**: Can start after Phase 2 and depends on the same core services, but remains independently testable
- **User Story 3 (US3)**: Can start after Phase 2 and relies on the same validation and UI infrastructure

### Parallel Opportunities

- T003 can run in parallel with T001 and T002 during Setup.
- T005, T006, and T007 can run in parallel after T004.
- US1, US2, and US3 all have separate independent test paths and can be implemented in parallel after the foundation is complete.
- T010/T011, T017/T018, and T023/T024 can all be executed in parallel within their respective user stories.

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks.
2. Implement User Story 1: successful conversion flow.
3. Validate conversion success, result display, and source/date metadata.
4. Then add User Story 2 and User Story 3 as independent reliability and validation layers.

### Incremental Delivery

1. Build and test the happy path first.
2. Add offline and missing-rate recovery.
3. Harden the validation and user-message layer.
4. Run end-to-end validation and documentation updates before release.
