"""Finance tools: stock/ETF price lookups via Yahoo Finance (no API key required)."""

from datetime import datetime, timedelta
from typing import Any

import httpx

# Yahoo Finance v8 quote endpoint — no auth required
_YF_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# Preset watchlist: common S&P 500 ETFs
DEFAULT_TICKERS: list[str] = ["SPY", "VOO", "IVV", "QQQ", "VTI"]


def _fetch_quote(symbol: str) -> dict[str, Any]:
    url = _YF_BASE.format(symbol=symbol.upper())
    headers = {"User-Agent": "Mozilla/5.0"}
    with httpx.Client(timeout=10) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    meta: dict[str, Any] = data["chart"]["result"][0]["meta"]
    return {
        "symbol": meta.get("symbol", symbol.upper()),
        "currency": meta.get("currency", "USD"),
        "price": meta.get("regularMarketPrice"),
        "previous_close": meta.get("chartPreviousClose"),
        "change": round(
            meta.get("regularMarketPrice", 0) - meta.get("chartPreviousClose", 0), 2
        ),
        "change_pct": round(
            (
                (meta.get("regularMarketPrice", 0) - meta.get("chartPreviousClose", 0))
                / meta.get("chartPreviousClose", 1)
            )
            * 100,
            2,
        ),
        "market_state": meta.get("marketState", "UNKNOWN"),
        "exchange": meta.get("exchangeName", ""),
    }


def get_etf_price(symbol: str) -> dict[str, Any]:
    """Get current price and daily change for a stock or ETF symbol (e.g. SPY, VOO, AAPL)."""
    return _fetch_quote(symbol)


def get_market_snapshot(tickers: list[str] | None = None) -> list[dict[str, Any]]:
    """Get a price snapshot for multiple tickers. Defaults to SPY, VOO, IVV, QQQ, VTI."""
    symbols = tickers if tickers else DEFAULT_TICKERS
    results = []
    for sym in symbols:
        try:
            results.append(_fetch_quote(sym))
        except Exception as e:
            results.append({"symbol": sym, "error": str(e)})
    return results


def get_weekly_performance(symbol: str) -> dict[str, Any]:
    """Get weekly performance for a stock/ETF (7 days ago vs current price)."""
    try:
        # Get current price
        current_data = _fetch_quote(symbol)
        current_price = current_data.get("price", 0)

        # Calculate timestamps for weekly data (5 trading days back)
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        period1 = int(week_ago.timestamp())
        period2 = int(now.timestamp())

        # Fetch historical data
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&period1={period1}&period2={period2}"
        headers = {"User-Agent": "Mozilla/5.0"}

        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        result = data["chart"]["result"][0]

        # Get the first close price from the week
        quotes = result.get("indicators", {}).get("quote", [{}])[0]
        close_prices = quotes.get("close", [])

        # Filter out None values and get the first valid close
        valid_closes = [p for p in close_prices if p is not None]

        if not valid_closes or current_price == 0:
            return {
                "symbol": symbol.upper(),
                "current_price": current_price,
                "week_ago_price": None,
                "weekly_change_pct": None,
                "error": "Insufficient data for weekly calculation"
            }

        week_ago_price = valid_closes[0]
        weekly_change = current_price - week_ago_price
        weekly_change_pct = (weekly_change / week_ago_price) * 100 if week_ago_price != 0 else 0

        return {
            "symbol": symbol.upper(),
            "current_price": current_price,
            "week_ago_price": round(week_ago_price, 2),
            "weekly_change": round(weekly_change, 2),
            "weekly_change_pct": round(weekly_change_pct, 2),
            "daily_change_pct": current_data.get("change_pct", 0)
        }
    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "error": str(e)
        }
