"""Daily summary tool: combines Israeli news, tech news, and key ETF prices."""

from typing import Any

from tools.finance import get_weekly_performance
from tools.news.news import get_israeli_news, get_tech_news, get_world_news


def get_daily_summary(
    news_limit: int = 3, etf_symbols: list[str] | None = None
) -> dict[str, Any]:
    """
    Get a comprehensive daily summary including:
    - Israeli news headlines
    - Tech news headlines
    - Stock/ETF prices with weekly performance

    Args:
        news_limit: Number of articles per source (default: 3)
        etf_symbols: List of symbols to track (default: ETFs + major tech stocks)

    Returns:
        Dictionary containing israeli_news, tech_news, and market_data with weekly performance
    """
# Default: ETFs + Major Tech Stocks (NVIDIA, Google, Meta)
    symbols = etf_symbols if etf_symbols else ["BITO", "VOO", "QQQ", "TQQQ", "NVDA", "GOOGL", "META"]

    # Fetch all data
    israeli_news = get_israeli_news(limit_per_source=news_limit)
    tech_news = get_tech_news(limit_per_source=news_limit)
    world_news = get_world_news(limit_per_source=news_limit)

    # Fetch weekly performance data for each symbol
    market_data = []
    for symbol in symbols:
        try:
            weekly_data = get_weekly_performance(symbol)
            market_data.append(weekly_data)
        except Exception as e:
            market_data.append({"symbol": symbol, "error": str(e)})

    return {
        "israeli_news": israeli_news,
        "tech_news": tech_news,
        "world_news": world_news,
        "market_data": market_data,
    }
