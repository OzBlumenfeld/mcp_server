"""Unit tests for Strava tools (mocked HTTP + env vars)."""

from unittest.mock import MagicMock, patch

import pytest

from tools.strava import _meters_to_km, _seconds_to_hms, get_recent_activities


def test_meters_to_km() -> None:
    assert _meters_to_km(5000) == 5.0
    assert _meters_to_km(1234) == 1.23


def test_seconds_to_hms() -> None:
    assert _seconds_to_hms(3661) == "01:01:01"
    assert _seconds_to_hms(0) == "00:00:00"
    assert _seconds_to_hms(7200) == "02:00:00"


@patch("tools.strava._get_access_token", return_value="fake_token")
@patch("tools.strava.httpx.Client")
def test_get_recent_activities(mock_client_cls: MagicMock, _mock_token: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "name": "Morning Run",
            "type": "Run",
            "start_date_local": "2026-03-10T07:00:00Z",
            "distance": 10000,
            "moving_time": 3600,
            "total_elevation_gain": 50,
            "average_heartrate": 145,
            "kudos_count": 3,
        }
    ]
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    results = get_recent_activities(limit=1)

    assert len(results) == 1
    assert results[0]["name"] == "Morning Run"
    assert results[0]["distance_km"] == 10.0
    assert results[0]["duration"] == "01:00:00"


def test_get_access_token_raises_without_env() -> None:
    from tools.strava import _get_access_token

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="Missing Strava credentials"):
            _get_access_token()
