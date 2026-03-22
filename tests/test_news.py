"""Tests for news tools."""

from unittest.mock import MagicMock, patch

from tools.news import get_hebrew_wikipedia_topic


def _make_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_get_hebrew_wikipedia_topic_success() -> None:
    """Test successful fetch of Hebrew Wikipedia featured article."""
    fake_data = {
        "tfa": {
            "titles": {"display": "כותרת המאמר"},
            "extract": "תקציר המאמר.",
            "content_urls": {"desktop": {"page": "https://he.wikipedia.org/wiki/Example"}},
            "originalimage": {"source": "https://upload.wikimedia.org/example.jpg"},
        }
    }
    with patch("tools.news.httpx.get", return_value=_make_response(fake_data)):
        result = get_hebrew_wikipedia_topic()

    assert result["title"] == "כותרת המאמר"
    assert result["extract"] == "תקציר המאמר."
    assert result["url"] == "https://he.wikipedia.org/wiki/Example"
    assert result["image_url"] == "https://upload.wikimedia.org/example.jpg"


def test_get_hebrew_wikipedia_topic_no_tfa() -> None:
    """Test response when no featured article is available."""
    with patch("tools.news.httpx.get", return_value=_make_response({})):
        result = get_hebrew_wikipedia_topic()

    assert "error" in result


def test_get_hebrew_wikipedia_topic_no_image() -> None:
    """Test featured article without image."""
    fake_data = {
        "tfa": {
            "titles": {"display": "כותרת"},
            "extract": "תקציר.",
            "content_urls": {"desktop": {"page": "https://he.wikipedia.org/wiki/Example"}},
        }
    }
    with patch("tools.news.httpx.get", return_value=_make_response(fake_data)):
        result = get_hebrew_wikipedia_topic()

    assert result["title"] == "כותרת"
    assert "image_url" not in result


def test_get_hebrew_wikipedia_topic_network_error() -> None:
    """Test graceful handling of network errors."""
    with patch("tools.news.httpx.get", side_effect=Exception("Connection error")):
        result = get_hebrew_wikipedia_topic()

    assert "error" in result
    assert "Connection error" in result["error"]
