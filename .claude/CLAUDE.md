# MCP Server Project Instructions

## Project Structure
* **`utils.py`** — shared validation helpers and type aliases (e.g., `OptStr`). Keep utility/type definitions here, not in `server.py`.
* **`server.py`** — MCP app wiring only: tool registration, env setup, logging init. No business logic or type utilities.
* **`tools/`** — one module per domain (news, finance, strava, etc.).

Write public functions first.

## Testing Guidelines

### Mock Tests
**DO NOT create or maintain mock tests** for external services like:
- RSS feeds (news sources)
- Yahoo Finance API
- Strava API
- Any third-party APIs

**Rationale:**
- Mock tests don't validate actual integration behavior
- External services change independently (e.g., RSS feeds going offline)
- Mocks create false confidence and maintenance burden
- Real integration issues are only caught with actual API calls

### Preferred Testing Approach
- Write **integration tests** only when needed for critical business logic
- Test internal data transformations and business rules
- Focus on code that we control, not external dependencies
- If external APIs are flaky, that's expected - don't mock around it

### Unit Tests That Are Acceptable
- Internal utility functions (e.g., HTML cleaning, data formatting)
- Business logic calculations
- Data structure transformations
- Internal service methods that don't call external APIs
