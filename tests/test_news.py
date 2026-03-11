"""Unit tests for news tools (mocked feedparser)."""

from unittest.mock import MagicMock, patch

from tools.news import get_israeli_news, get_tech_news


def _make_feed(entries: list[dict[str, str]]) -> MagicMock:
    mock_feed = MagicMock()
    mock_entries = []
    for e in entries:
        entry = MagicMock()
        entry.get = lambda key, default="", _e=e: _e.get(key, default)
        mock_entries.append(entry)
    mock_feed.entries = mock_entries
    return mock_feed


@patch("tools.news.feedparser.parse")
def test_get_israeli_news_returns_all_sources(mock_parse: MagicMock) -> None:
    mock_parse.return_value = _make_feed(
        [{"title": "Test", "link": "http://x.com", "summary": "Summary"}]
    )

    results = get_israeli_news(limit_per_source=1)

    assert len(results) == 3
    sources = [r["source"] for r in results]
    assert "Times of Israel" in sources
    assert "Haaretz" in sources
    assert "Ynet" in sources


@patch("tools.news.feedparser.parse")
def test_get_tech_news_returns_all_sources(mock_parse: MagicMock) -> None:
    mock_parse.return_value = _make_feed(
        [{"title": "Tech Story", "link": "http://hn.com", "summary": "Details"}]
    )

    results = get_tech_news(limit_per_source=1)

    assert len(results) == 3
    sources = [r["source"] for r in results]
    assert "Hacker News" in sources
    assert "TechCrunch" in sources
    assert "The Verge" in sources


@patch("tools.news.feedparser.parse")
def test_limit_per_source_respected(mock_parse: MagicMock) -> None:
    entries = [
        {"title": f"Article {i}", "link": f"http://x.com/{i}", "summary": ""}
        for i in range(10)
    ]
    mock_parse.return_value = _make_feed(entries)

    results = get_israeli_news(limit_per_source=2)

    for src in results:
        assert len(src["articles"]) <= 2
