"""Finance tools: stock/ETF price lookups via Yahoo Finance (no API key required)."""

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
