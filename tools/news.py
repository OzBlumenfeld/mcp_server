"""News tools: Israeli news and tech TL;DR via RSS feeds."""

from typing import Any

import feedparser

NEWS = "news"
TECH = "tech"
WORLD = "world"

FEEDS: dict[str, list[dict[str, str]]] = {
    NEWS: [
        {"name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/"},
        {"name": "Ynet", "url": "https://www.ynet.co.il/Integration/StoryRss2.xml"},
    ],
    TECH: [
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    ],
    WORLD: [
        {"name": "CNN", "url": "http://rss.cnn.com/rss/cnn_topstories.rss"},
    ],
}


def _truncate_at_sentence(text: str, max_length: int = 300) -> str:
    """Truncate text at sentence boundary, not mid-sentence."""
    if len(text) <= max_length:
        return text

    # Truncate to max_length first
    truncated = text[:max_length]

    # Find the last sentence ending (period, exclamation, or question mark)
    # Look for sentence endings followed by space or end of string
    sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']

    last_sentence_pos = -1
    for ending in sentence_endings:
        pos = truncated.rfind(ending)
        if pos > last_sentence_pos:
            last_sentence_pos = pos

    # If we found a sentence ending, truncate there (include the punctuation)
    if last_sentence_pos > 0:
        return truncated[:last_sentence_pos + 1].strip()

    # If no sentence ending found, try to break at last complete word
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space].strip() + '...'

    # Fallback: just truncate and add ellipsis
    return truncated.strip() + '...'


def _parse_feed(url: str, limit: int) -> list[dict[str, str]]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        summary_text = entry.get("summary", entry.get("description", ""))
        items.append(
            {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "summary": _truncate_at_sentence(summary_text, 300),
            }
        )
    return items


def get_israeli_news(limit_per_source: int = 3) -> list[dict[str, Any]]:
    """Fetch top headlines from Israeli news sources (Times of Israel, Ynet)."""
    results: list[dict[str, Any]] = []
    for source in FEEDS[NEWS]:
        items = _parse_feed(source["url"], limit_per_source)
        if not items:
            print(f"No items found for source {source['name']}")
            continue
        results.append({"source": source["name"], "articles": items})
    return results


def get_tech_news(limit_per_source: int = 3) -> list[dict[str, Any]]:
    """Fetch top tech headlines from Hacker News, TechCrunch, and The Verge."""
    results: list[dict[str, Any]] = []
    for source in FEEDS[TECH]:
        items = _parse_feed(source["url"], limit_per_source)
        results.append({"source": source["name"], "articles": items})
    return results


def get_world_news(limit_per_source: int = 3) -> list[dict[str, Any]]:
    """Fetch top headlines from world news sources (CNN)."""
    results: list[dict[str, Any]] = []
    for source in FEEDS[WORLD]:
        items = _parse_feed(source["url"], limit_per_source)
        results.append({"source": source["name"], "articles": items})
    return results
