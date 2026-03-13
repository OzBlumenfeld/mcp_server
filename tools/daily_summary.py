"""Daily summary tool: combines Israeli news, tech news, and key ETF prices."""

from typing import Any

from tools.finance import get_etf_price
from tools.news import get_israeli_news, get_tech_news


def get_daily_summary(
    news_limit: int = 3, etf_symbols: list[str] | None = None
) -> dict[str, Any]:
    """
    Get a comprehensive daily summary including:
    - Israeli news headlines
    - Tech news headlines
    - ETF prices for BITO, SPY (S&P 500), and QQQ (Nasdaq)

    Args:
        news_limit: Number of articles per source (default: 3)
        etf_symbols: List of ETF symbols to track (default: ["BITO", "SPY", "QQQ"])

    Returns:
        Dictionary containing israeli_news, tech_news, and market_data
    """
    # Default ETFs: BITO (Bitcoin), SPY (S&P 500), QQQ (Nasdaq)
    symbols = etf_symbols if etf_symbols else ["BITO", "SPY", "QQQ"]

    # Fetch all data
    israeli_news = get_israeli_news(limit_per_source=news_limit)
    tech_news = get_tech_news(limit_per_source=news_limit)

    # Fetch ETF prices
    market_data = []
    for symbol in symbols:
        try:
            price_data = get_etf_price(symbol)
            market_data.append(price_data)
        except Exception as e:
            market_data.append({"symbol": symbol, "error": str(e)})

    return {
        "israeli_news": israeli_news,
        "tech_news": tech_news,
        "market_data": market_data,
    }
