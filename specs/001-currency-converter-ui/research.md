# Research: Currency Converter UI

## Decision: Use the official BNM XML feed as the default source

**Decision**: The application will prefer the official National Bank of Moldova (BNM) XML endpoint for live exchange rates because it is an authoritative source, is published on working days, and matches the project requirement for a legitimate rate source without requiring a paid commercial service.

**Rationale**: The project specification explicitly notes that BNM publishes the rate in XML on a stable URL and that there is no JSON endpoint. This provides a deterministic source with clear date semantics and explicit rate validity windows.

**Alternatives considered**:
- Public free APIs: easier to consume but often rate-limited and less trustworthy for a student project due to inconsistent schema and availability.
- Manual parsing of other public pages: reduced reliability and more fragile change-management risk.

## Decision: Use local cache as the fallback and offline safety net

**Decision**: The app will persist the most recent successful response locally and reuse it when the network is unavailable or the selected day has no published rate.

**Rationale**: The specification requires graceful handling of offline conditions and missing-rate days, and it explicitly says the app should offer the user the last successful rate with its date. A cached rate is the clearest path to satisfy both requirements.

**Alternatives considered**:
- In-memory cache only: insufficient because the app must survive restarts.
- No cache: fails the offline requirement and degrades user trust.

## Decision: Keep the UI simple and validation-first

**Decision**: The GUI will contain exactly the required fields: amount, source currency, target currency, conversion button, result display, and source/date metadata.

**Rationale**: The specification defines a focused desktop workflow and a minimal interaction model. Trying to add extra features would increase complexity and contradict the maintainability principle.

**Alternatives considered**:
- Additional charts, historical trends, or multi-currency watchlists: valuable in a broader product but out-of-scope for the project and not required by the specification.

## Decision: Use Python with a small desktop stack

**Decision**: A Python desktop app with Tkinter is the best fit for a small, student-appropriate tool that requires a GUI without a large dependency surface.

**Rationale**: It allows quick local development, strong standard-library support for XML parsing and storage, and straightforward validation of edge cases.

**Alternatives considered**:
- Web app: would require browser tooling and a larger runtime stack than needed here.
- Qt or Electron: more overhead and not necessary for a focused conversion tool.

## Design implications

- The application must treat weekends and official holidays as missing rate periods and use the latest available data with a visible fallback notice.
- Retry behavior should be limited to a simple read of the latest cached or most recent valid rate, not a long series of retries.
- Validation should happen before any network or conversion logic executes to avoid silent errors or incorrect outputs.
- All rate-source fallback actions must be visible to the user so the application remains transparent and trustworthy.
