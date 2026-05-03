# Personal Assistant MCP Server

A FastMCP server that exposes tools for news aggregation, financial market data, fitness tracking, and email notifications — usable directly from Claude via the Model Context Protocol.

Also includes a **daily newsletter** that automatically emails a formatted digest of market data and news each morning via GitHub Actions.

## Features

- **News**: Multi-source aggregation via NewsAPI and RSS (Times of Israel, Ynet, Hacker News, TechCrunch, The Verge, NPR, BBC)
- **Finance**: Real-time ETF/stock prices and weekly performance via Yahoo Finance
- **Fitness**: Strava integration for recent activities and weekly training summaries
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

## Setup

### Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) enabled
- [NewsAPI](https://newsapi.org/) API key
- (Optional) Strava API credentials

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
│   ├── news.py           # RSS + NewsAPI aggregation
│   ├── finance.py        # Yahoo Finance integration
│   ├── strava.py         # Strava API integration
│   └── daily_summary.py  # Aggregated daily snapshot
├── tests/                # Unit tests
└── .github/workflows/    # GitHub Actions
```
