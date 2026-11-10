# Research: Currency Converter UI

## Decision: Use the official BNM XML feed as the only source

**Decision**: The application will use only the official National Bank of Moldova (BNM) XML endpoint for live exchange rates because it is an authoritative source, is published on working days, and matches the project requirement for a legitimate rate source without requiring a paid commercial service.

**Rationale**: The project specification explicitly notes that BNM publishes the rate in XML on a stable URL and that there is no JSON endpoint. This provides a deterministic source with clear date semantics and explicit rate validity windows.

**Alternatives considered**:
- Public free APIs and manual parsing of other public pages are out of scope; BNM XML is the single supported source.

## Decision: Use local cache as the fallback and offline safety net

**Decision**: The app will persist the most recent successful response locally and reuse it when the network is unavailable, XML is malformed, or no rates are found after checking today and the 10 preceding calendar days.

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

- The application must treat weekends and official holidays as missing rate periods, checking each previous calendar day through the 10-day limit and showing the effective date when an earlier rate is used.
- If fetching fails, XML is malformed, or the 10-day search returns no rates, use the last successful cached response when available and show its effective date.
- Validation should happen before any network or conversion logic executes to avoid silent errors or incorrect outputs.
- All rate-source fallback actions must be visible to the user so the application remains transparent and trustworthy.
