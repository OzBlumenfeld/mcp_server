# Personal Assistant MCP Server

A FastMCP server that exposes tools for news aggregation, financial market data, fitness tracking, Spotify music data, and email notifications — usable directly from Claude via the Model Context Protocol.

Also includes a **daily newsletter** that automatically emails a formatted digest of market data and news each morning via GitHub Actions.

## Features

- **News**: Multi-source aggregation via NewsAPI and RSS (Times of Israel, Ynet, Hacker News, TechCrunch, The Verge, NPR, BBC)
- **Finance**: Real-time ETF/stock prices and weekly performance via Yahoo Finance
- **Fitness**: Strava integration for recent activities and weekly training summaries
- **Music**: Spotify integration for top tracks and top podcasts based on recent listening
- **Email**: Gmail SMTP notifications with HTML support
- **Daily Newsletter**: Scheduled HTML digest email sent every morning at 7:00 AM UTC

## Tools Exposed via MCP

| Tool | Description |
|---|---|
| `send_email` | Send an email via Gmail SMTP |
| `fetch_news` | Fetch top headlines from NewsAPI (optional query/category) |
| `get_israeli_news` | Latest news from Israeli RSS sources |
| `get_tech_news` | Latest tech news from RSS sources |
| `get_daily_summary` | Combined snapshot of all news + market data |
| `get_etf_price` | Current price and daily change for a ticker |
| `get_market_snapshot` | Multi-ticker market overview |
| `get_recent_activities` | Recent Strava activities |
| `get_weekly_summary` | Weekly Strava training summary |
| `get_top_tracks` | Top tracks from the last ~4 weeks via Spotify |
| `get_top_podcasts` | Top podcasts ranked by recent play frequency via Spotify |

## Setup

### Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) enabled
- [NewsAPI](https://newsapi.org/) API key
- (Optional) Strava API credentials
- (Optional) Spotify app credentials (see [Spotify Setup](#spotify-setup))

### Install

```bash
uv sync
```

## Usage

### As an MCP Server (Claude integration)

The `.mcp.json` file registers this server with Claude Code automatically. Once configured, the tools above are available directly in your Claude conversations.

To start the server manually:

```bash
uv run python server.py
```

For SSE transport (HTTP server on port 9005):

```bash
MCP_TRANSPORT=sse uv run python server.py
```

### Send a daily newsletter manually

```bash
uv run python on_demand.py
```

### With timeout protection

```bash
uv run python safe_runner.py
```

### Inspect with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run python server.py
```

## Spotify Setup

Spotify requires OAuth — a one-time setup to obtain a refresh token.

### 1. Create a Spotify App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Under **Edit Settings**, add `http://127.0.0.1:8888/callback` as a Redirect URI.
3. Copy your **Client ID** and **Client Secret** into `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

### 2. Get a Refresh Token

Run the one-time authorization script:

```bash
uv run tools/spotify/get_refresh_token.py
```

This opens a browser tab for Spotify authorization. After you approve, the script prints your refresh token. Add it to `.env`:

```env
SPOTIFY_REFRESH_TOKEN=your_refresh_token
```

The required OAuth scopes are `user-top-read` and `user-read-recently-played`.

### Tools

| Tool | Scope required | Description |
|---|---|---|
| `get_top_tracks` | `user-top-read` | Top tracks over the last ~4 weeks, ranked by Spotify |
| `get_top_podcasts` | `user-read-recently-played` | Top podcast shows ranked by episode play count in the last 50 recently-played items |

## Daily Newsletter (GitHub Actions)

The workflow at [.github/workflows/daily-newsletter.yml](.github/workflows/daily-newsletter.yml) runs every day at **7:00 AM UTC** and sends an HTML email digest containing:

- Market snapshot with daily and weekly performance for key ETFs
- Israeli news highlights
- World news highlights
- Tech news highlights

## Development

```bash
# Lint
uv run ruff check . --fix

# Run tests
uv run pytest
```

Tests cover internal utilities and data transformations. Mock tests for external APIs (NewsAPI, Yahoo Finance, Strava) are intentionally avoided — see [.claude/CLAUDE.md](.claude/CLAUDE.md) for rationale.

## Project Structure

```
├── server.py             # FastMCP server entry point
├── on_demand.py          # Daily newsletter generator
├── email_sender.py       # Gmail SMTP client
├── safe_runner.py        # Timeout-protected newsletter runner
├── logging_config.py     # Structured JSON logging
├── cost_estimate.py      # Monthly cloud cost estimator
├── tools/
│   ├── news/
│   │   ├── news.py       # RSS + NewsAPI aggregation
│   │   └── on_demand.py  # Manual newsletter trigger
│   ├── spotify/
│   │   ├── spotify.py          # Spotify API integration
│   │   ├── get_refresh_token.py # One-time OAuth token setup
│   │   └── on_demand.py        # Manual Spotify runner
│   ├── finance.py        # Yahoo Finance integration
│   ├── strava.py         # Strava API integration
│   └── daily_summary.py  # Aggregated daily snapshot
├── tests/                # Unit tests
└── .github/workflows/    # GitHub Actions
```
