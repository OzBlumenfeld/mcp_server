"""News tools: Israeli news and tech TL;DR via RSS feeds."""

from typing import Any

import feedparser

FEEDS: dict[str, list[dict[str, str]]] = {
    "israeli": [
        {"name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/"},
        {"name": "Haaretz", "url": "https://www.haaretz.com/srv/haaretz-israel-news"},
        {"name": "Ynet", "url": "https://www.ynet.co.il/Integration/StoryRss2.xml"},
    ],
    "tech": [
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    ],
}


def _parse_feed(url: str, limit: int) -> list[dict[str, str]]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        items.append(
            {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", ""))[:300],
            }
        )
    return items


def get_israeli_news(limit_per_source: int = 3) -> list[dict[str, Any]]:
    """Fetch top headlines from Israeli news sources (Times of Israel, Haaretz, Ynet)."""
    results: list[dict[str, Any]] = []
    for source in FEEDS["israeli"]:
        items = _parse_feed(source["url"], limit_per_source)
        results.append({"source": source["name"], "articles": items})
    return results


def get_tech_news(limit_per_source: int = 3) -> list[dict[str, Any]]:
    """Fetch top tech headlines from Hacker News, TechCrunch, and The Verge."""
    results: list[dict[str, Any]] = []
    for source in FEEDS["tech"]:
        items = _parse_feed(source["url"], limit_per_source)
        results.append({"source": source["name"], "articles": items})
    return results
