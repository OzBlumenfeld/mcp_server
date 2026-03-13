"""Tests for daily summary tool."""

from unittest.mock import patch

from tools.daily_summary import get_daily_summary


def test_get_daily_summary_structure() -> None:
    """Test that get_daily_summary returns the correct structure."""
    with patch("tools.daily_summary.get_israeli_news") as mock_israeli, \
         patch("tools.daily_summary.get_tech_news") as mock_tech, \
         patch("tools.daily_summary.get_etf_price") as mock_etf:

        mock_israeli.return_value = [{"source": "Test Israeli", "articles": []}]
        mock_tech.return_value = [{"source": "Test Tech", "articles": []}]
        mock_etf.return_value = {
            "symbol": "SPY",
            "price": 500.0,
            "change": 5.0,
            "change_pct": 1.0
        }

        result = get_daily_summary()

        assert "israeli_news" in result
        assert "tech_news" in result
        assert "market_data" in result
        assert len(result["market_data"]) == 3  # BITO, SPY, QQQ


def test_get_daily_summary_custom_symbols() -> None:
    """Test get_daily_summary with custom ETF symbols."""
    with patch("tools.daily_summary.get_israeli_news") as mock_israeli, \
         patch("tools.daily_summary.get_tech_news") as mock_tech, \
         patch("tools.daily_summary.get_etf_price") as mock_etf:

        mock_israeli.return_value = []
        mock_tech.return_value = []
        mock_etf.return_value = {"symbol": "AAPL", "price": 150.0}

        result = get_daily_summary(news_limit=5, etf_symbols=["AAPL", "MSFT"])

        assert len(result["market_data"]) == 2
        mock_israeli.assert_called_once_with(limit_per_source=5)
        mock_tech.assert_called_once_with(limit_per_source=5)


def test_get_daily_summary_handles_etf_errors() -> None:
    """Test that get_daily_summary handles ETF fetch errors gracefully."""
    with patch("tools.daily_summary.get_israeli_news") as mock_israeli, \
         patch("tools.daily_summary.get_tech_news") as mock_tech, \
         patch("tools.daily_summary.get_etf_price") as mock_etf:

        mock_israeli.return_value = []
        mock_tech.return_value = []
        mock_etf.side_effect = Exception("Network error")

        result = get_daily_summary()

        assert "market_data" in result
        # All three ETF calls should fail and be caught
        for item in result["market_data"]:
            assert "error" in item
