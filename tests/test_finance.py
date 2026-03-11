"""Unit tests for finance tools (mocked HTTP)."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tools.finance import get_etf_price, get_market_snapshot


def _mock_chart_response(symbol: str, price: float, prev_close: float) -> dict[str, Any]:
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": symbol,
                        "currency": "USD",
                        "regularMarketPrice": price,
                        "chartPreviousClose": prev_close,
                        "marketState": "REGULAR",
                        "exchangeName": "NYSE",
                    }
                }
            ]
        }
    }


@patch("tools.finance.httpx.Client")
def test_get_etf_price_returns_expected_fields(mock_client_cls: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = _mock_chart_response("SPY", 510.0, 505.0)
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    result = get_etf_price("SPY")

    assert result["symbol"] == "SPY"
    assert result["price"] == 510.0
    assert result["previous_close"] == 505.0
    assert result["change"] == 5.0
    assert result["change_pct"] == pytest.approx(0.99, rel=1e-2)


@patch("tools.finance.httpx.Client")
def test_get_market_snapshot_default_tickers(mock_client_cls: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = _mock_chart_response("SPY", 510.0, 505.0)
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    results = get_market_snapshot()
    assert len(results) == 5


@patch("tools.finance.httpx.Client")
def test_get_market_snapshot_custom_tickers(mock_client_cls: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = _mock_chart_response("AAPL", 200.0, 198.0)
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    results = get_market_snapshot(["AAPL", "MSFT"])
    assert len(results) == 2


@patch("tools.finance.httpx.Client")
def test_get_market_snapshot_handles_error(mock_client_cls: MagicMock) -> None:
    mock_client_cls.return_value.__enter__.return_value.get.side_effect = Exception(
        "Network error"
    )

    results = get_market_snapshot(["FAIL"])
    assert results[0]["symbol"] == "FAIL"
    assert "error" in results[0]
