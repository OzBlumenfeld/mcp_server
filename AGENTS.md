# GitHub Copilot Instructions for MCP Server

**Purpose**: This file provides GitHub Copilot with project context, architecture patterns, and development conventions. It is automatically loaded on every interaction with this workspace.

---

## Quick Reference

| Aspect | Value |
|--------|-------|
| **Language** | Python 3.12+ (< 3.14) |
| **Framework** | FastMCP 3.1.0 |
| **Package Manager** | `uv` (astral.sh) |
| **Async Runtime** | asyncio |
| **Testing Framework** | pytest 9.0.2+ |
| **Linter/Formatter** | ruff 0.9.0+ |
| **External Shared Types** | `oz-shared[postgres]` (GitHub: ozblumenfeld/oz-shared) |

---

## Architecture Overview

This is a **FastMCP server** that exposes tools for third-party integrations and notifications, usable directly from Claude via the Model Context Protocol.

### High-Level Flow

```
Claude (via MCP)
    ↓
server.py (tool registration, env setup, logging)
    ↓
tools/ (business logic per domain)
    ├── news/ (NewsAPI, RSS feeds)
    ├── finance/ (Yahoo Finance)
    ├── strava/ (Strava OAuth)
    ├── spotify/ (Spotify OAuth)
    ├── calendar/ (Google Calendar OAuth)
    └── daily_summary.py (aggregates all tools)
    ↓
External APIs (NewsAPI, Yahoo Finance, Strava, Spotify, Google Calendar, Gmail SMTP)
```

### Key Design Principle

- **server.py** = MCP wiring only (tool registration, secrets loading, logging)
- **utils.py** = Type aliases and validation helpers (e.g., `OptStr`)
- **tools/** = Business logic; one module per domain/service
- **tests/** = Integration tests (real API calls where applicable)
- **db.py, logging_config.py** = Infrastructure utilities
- **email_sender.py** = Gmail SMTP wrapper

---

## Project Structure

```
mcp_server/
├── server.py                 # Tool registration, env setup, logging init
├── utils.py                  # Type aliases (OptStr), shared validators
├── db.py                     # Database utilities
├── logging_config.py         # Logging configuration
├── email_sender.py           # Gmail SMTP wrapper
├── pyproject.toml            # Dependencies and project metadata
├── Dockerfile                # Docker configuration
├── README.md                 # User-facing documentation
├── .env                      # Local secrets (not in git)
│
├── tools/                    # Business logic modules
│   ├── __init__.py
│   ├── daily_summary.py      # Aggregates news, finance, fitness, music
│   ├── finance.py            # Yahoo Finance integration
│   ├── news.py               # NewsAPI and RSS feeds
│   ├── strava.py             # Strava API + OAuth
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── gcal.py           # Google Calendar fetch
│   │   ├── get_refresh_token.py
│   │   └── on_demand.py
│   ├── news/
│   │   ├── __init__.py
│   │   ├── news.py
│   │   └── on_demand.py
│   └── spotify/
│       ├── __init__.py
│       ├── spotify.py        # Spotify API + OAuth
│       ├── get_refresh_token.py
│       └── on_demand.py
│
├── tests/                    # Integration and unit tests
│   ├── __init__.py
│   ├── test_daily_summary.py
│   ├── test_finance.py
│   ├── test_strava.py
│   └── response.json         # Mock response fixture
│
└── .claude/
    └── CLAUDE.md             # Claude-specific instructions (Claude IDE only)
```

---

## Code Organization Rules

### Where Things Go

| **Category** | **Location** | **Examples** |
|---|---|---|
| **Type aliases & validation** | `utils.py` | `OptStr`, `validate_ticker()` |
| **Business logic** | `tools/<domain>.py` | `fetch_news()`, `get_etf_price()`, `get_top_tracks()` |
| **Tool registration & wiring** | `server.py` | `@mcp.tool` decorators, environment setup, logging init |
| **Infrastructure** | Root level files | `db.py`, `logging_config.py`, `email_sender.py` |
| **Tests** | `tests/` | Integration and unit tests |

### Function Organization

**Write public functions first**, then internal helpers.

```python
# tools/finance.py
async def get_etf_price(ticker: str) -> dict:
    """Public function: fetch ETF price from Yahoo Finance."""
    ...

async def _fetch_from_yahoo(ticker: str) -> dict:
    """Internal helper: handle API call."""
    ...
```

### Imports & Type Hints

- Use type hints everywhere (async functions, tool parameters)
- Import shared types from `oz_shared.types` (e.g., `OptStr`)
- Use `logging` module for all debug/info/error logging
- Follow PEP 8 via ruff

---

## Testing Philosophy

### **DO NOT create or maintain mock tests** for external services

**External services to NEVER mock:**
- RSS feeds (news sources)
- Yahoo Finance API
- Strava API
- Spotify API
- Google Calendar API
- NewsAPI
- Gmail SMTP

**Why?**
- Mock tests don't validate actual integration behavior
- External services change independently (RSS feeds go offline, API versions change)
- Mocks create false confidence and maintenance burden
- Real integration issues are only caught with actual API calls

### Preferred Testing Approach

**Write integration tests** for critical business logic:
- Call real external APIs in tests (mocked authentication via `.env` test credentials)
- Test data transformations and formatting (HTML cleaning, aggregation logic)
- Test internal database queries
- Test error handling with real failure scenarios

**Example**: `test_finance.py` calls Yahoo Finance and validates the response structure, not a mock.

### What to Test

✅ Internal utility functions (HTML cleaning, data formatting)  
✅ Business logic calculations (weekly averages, aggregation)  
✅ Data structure transformations  
✅ Database operations  
✅ Error handling edge cases  

❌ Mocking third-party API responses  
❌ Mocking OAuth flows (use real tokens in tests)  
❌ Mocking database connections (use real test database)

---

## Adding a New Tool

### Checklist

1. **Create the module** in `tools/<domain>.py`
   ```python
   # tools/example.py
   import logging
   from oz_shared.types import OptStr
   
   logger = logging.getLogger(__name__)
   
   async def get_example_data(param: str) -> dict:
       """Fetch data from Example API."""
       # Public function first
       ...
   ```

2. **Write public function first**, then internal helpers
   - Document docstring with tool description (used by MCP)
   - Use async/await
   - Return dict or str
   - Add logging for debugging

3. **Register in `server.py`**
   ```python
   from tools.example import get_example_data
   
   @mcp.tool
   async def get_example_data(param: str) -> dict:
       """Fetch data from Example API."""
       return await get_example_data(param)
   ```

4. **Add tests in `tests/test_example.py`**
   - Use real API calls (not mocks)
   - Test with actual credentials from `.env`
   - Validate response structure
   - Test error cases if applicable

5. **Update README.md** with the new tool in the Tools table

---

## Environment Setup

### Required Secrets (.env file)

Create `.env` in the root directory (git-ignored):

```bash
# Email (Gmail App Password)
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-app-password

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio phone number in E.164 format

# News API
NEWSAPI_KEY=your-newsapi-key

# Strava (OAuth)
STRAVA_CLIENT_ID=your-strava-client-id
STRAVA_CLIENT_SECRET=your-strava-secret
STRAVA_REFRESH_TOKEN=your-refresh-token

# Spotify (OAuth)
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-secret
SPOTIFY_REFRESH_TOKEN=your-refresh-token

# Google Calendar (OAuth)
GOOGLE_CALENDAR_REFRESH_TOKEN=your-google-refresh-token

# 1Password (via oz-shared)
OP_SERVICE_ACCOUNT_TOKEN=your-1password-token  # Optional, for secret vaults
```

### Secret Loading

The project uses `oz-shared` for secret management:

```python
from oz_shared.onepassword import load_op_secrets

# In server.py:
asyncio.run(load_op_secrets())  # Loads 1Password secrets if configured
```

For local development, `.env` is loaded automatically:
```python
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
```

### Installation

```bash
uv sync  # Install all dependencies from pyproject.toml
```

---

## Common Commands

### Development

```bash
# Install dependencies
uv sync

# Run the MCP server locally
python server.py

# Run server with SSE transport (HTTP on port 9005)
MCP_TRANSPORT=sse python server.py

# Inspect with MCP Inspector
mcp dev server.py

# Send daily newsletter manually
python tools/daily_summary.py

# Run with timeout protection
python safe_runner.py
```

### Testing & Linting

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_finance.py

# Run with verbose output
pytest -v

# Check code style with ruff
ruff check .

# Format code with ruff
ruff format .

# Fix linting issues automatically
ruff check --fix .
```

---

## External Integrations

| **Service** | **Purpose** | **Key Files** | **Auth Type** |
|---|---|---|---|
| **NewsAPI** | Fetch top headlines by category or query | `tools/news/news.py` | API Key |
| **Yahoo Finance** | Real-time ETF/stock prices and performance | `tools/finance.py` | Public API (no auth) |
| **Strava** | Recent activities and weekly training summaries | `tools/strava.py` | OAuth 2.0 |
| **Spotify** | Top tracks and top podcasts | `tools/spotify/spotify.py` | OAuth 2.0 |
| **Google Calendar** | Fetch calendar events | `tools/calendar/gcal.py` | OAuth 2.0 |
| **Gmail SMTP** | Send HTML emails | `email_sender.py` | App Password |
| **Twilio SMS** | Send SMS messages (WhatsApp support planned) | `sms_sender.py` | Account SID + Auth Token |

### OAuth Token Refresh

For services requiring OAuth (Strava, Spotify, Google Calendar):
- Initial token setup: `tools/<service>/get_refresh_token.py`
- Token refresh: handled automatically by `oz-shared` or in tool function
- Tokens stored in `.env` as `<SERVICE>_REFRESH_TOKEN`

---

## Notification Senders

### Email (Gmail SMTP)

Use `EmailNotificationSender` to send emails with optional HTML formatting:

```python
from email_sender import EmailNotificationSender

email_sender = EmailNotificationSender()
success = await email_sender.send_email(
    recipient_email="user@example.com",
    subject="Hello",
    body="Plain text message",
    html_body="<h1>Hello</h1><p>HTML message</p>"  # Optional
)
```

**Environment Variables**: `GMAIL_SENDER_EMAIL`, `GMAIL_APP_PASSWORD`

### SMS (Twilio)

Use `SMSNotificationSender` to send SMS messages via Twilio. Designed to support multiple channels (SMS now, WhatsApp in the future):

```python
from sms_sender import SMSNotificationSender

sms_sender = SMSNotificationSender()
success = await sms_sender.send_sms(
    recipient_phone="+1234567890",  # E.164 format
    message="Your verification code is 123456"
)
```

**Environment Variables**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

**Future Multi-Channel Support**: The SMS sender is designed to extend to WhatsApp by prefixing the phone number:
```python
# Future: Send via WhatsApp instead
await sms_sender.send_sms(
    recipient_phone="whatsapp:+1234567890",
    message="Message via WhatsApp"
)
```

---

## Key Patterns

### Async/Await

All tool functions are `async`:

```python
@mcp.tool
async def get_data(query: str) -> dict:
    """Tool description for MCP."""
    return await fetch_from_api(query)
```

### Logging

Use the `logging` module consistently:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing query", extra={"query": query})
logger.error("API error", extra={"status": response.status_code})
```

Logging is configured in `logging_config.py` and initialized in `server.py`.

### Type Hints

Use type hints everywhere; import from `oz_shared.types`:

```python
from oz_shared.types import OptStr

async def fetch_news(query: OptStr = None, category: str = "general") -> dict:
    """Fetch news with optional query."""
    ...
```

Common types:
- `OptStr` = `str | None`
- `Dict`, `List`, `Optional` from `typing`

### Error Handling

Handle API errors gracefully, log them, and return structured responses:

```python
try:
    response = await httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
except httpx.HTTPError as e:
    logger.error("API request failed", extra={"url": url, "error": str(e)})
    raise ValueError(f"Failed to fetch data: {e}")
```

### HTTP Client

Use `httpx` for HTTP requests:

```python
import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
```

---

## MCP Tool Requirements

### Tool Definition

Every tool exposed to Claude via MCP must:
1. Be an `async` function
2. Have a clear docstring (first line is the tool description)
3. Be decorated with `@mcp.tool`
4. Have type hints on all parameters and return value
5. Return a simple type: `str`, `dict`, or `list`

### Example

```python
# In server.py
from tools.news import fetch_news

@mcp.tool
async def fetch_news(query: OptStr = None, category: str = "general") -> str:
    """Fetch top news headlines by category or search query."""
    result = await fetch_news(query, category)
    return json.dumps(result)
```

---

## Debugging & Troubleshooting

### Check Logging

Logs are configured to show INFO and DEBUG levels. Review `logging_config.py` to adjust.

```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Fetched {len(items)} items from API")
```

### Test a Tool Manually

```bash
python -c "
import asyncio
from tools.finance import get_etf_price
print(asyncio.run(get_etf_price('SPY')))
"
```

### Inspect MCP Server

```bash
mcp dev server.py
```

Opens MCP Inspector at `http://localhost:3000` to test tools interactively.

---

## Dependencies & Maintenance

### Key Dependencies

- **fastmcp** (3.1.0) — MCP server framework
- **httpx** (0.28.1+) — Async HTTP client
- **feedparser** (6.0.12+) — RSS feed parsing
- **python-dotenv** (1.2.1+) — Load .env files
- **oz-shared[postgres]** — Type aliases, database utilities, secret management

### Dev Dependencies

- **pytest** (9.0.2+) — Testing framework
- **ruff** (0.9.0+) — Linting and formatting

### Updating Dependencies

```bash
# Update everything
uv sync --upgrade

# Update specific package
uv pip install --upgrade fastmcp
```

---

## Additional Resources

- **FastMCP Docs**: https://github.com/jlouis/fastmcp
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **NewsAPI**: https://newsapi.org/
- **Yahoo Finance**: https://finance.yahoo.com/
- **Strava API**: https://developers.strava.com/
- **Spotify API**: https://developer.spotify.com/
- **Google Calendar API**: https://developers.google.com/calendar
- **oz-shared Repo**: https://github.com/ozblumenfeld/oz-shared
- **Project README**: See [README.md](README.md) for user-facing documentation

---

**Last Updated**: 2026-08-15  
**For Claude IDE Only**: Also see [.claude/CLAUDE.md](.claude/CLAUDE.md) for Claude-specific guidelines.
