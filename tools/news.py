"""News tools: Israeli news and tech TL;DR via RSS feeds."""

import re
from datetime import datetime, timezone
from html import unescape
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
        {"name": "NPR", "url": "https://feeds.npr.org/1001/rss.xml"},
        {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
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


def _extract_image_url(entry: Any) -> str | None:
    """Extract image URL from RSS feed entry."""
    # Try media:content or media:thumbnail (common in RSS feeds)
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url')

    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')

    # Try enclosure tag (podcasts and some news feeds)
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            # Check if it's an image type
            if enclosure.get('type', '').startswith('image/'):
                return enclosure.get('href') or enclosure.get('url')

    # Try links with image type
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                return link.get('href')

    # Try to extract image from content/description HTML
    content = entry.get('content', [{}])[0].get('value', '') if hasattr(entry, 'content') else ''
    if not content:
        content = entry.get('summary', '') or entry.get('description', '')

    if content:
        # Look for <img> tags in the content
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if img_match:
            return img_match.group(1)

    return None


def _clean_summary(raw_html: str) -> str:
    """Clean HTML from summary and discard if it's just a navigation link (e.g. HN 'Comments')."""
    text = re.sub(r'<[^>]+/?>', '', raw_html)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Discard summaries that are just noise (e.g. Hacker News "Comments" link)
    if text.lower() in {"comments", ""}:
        return ""
    return text


_MAX_AGE_DAYS = 7


def _is_recent(entry: Any) -> bool:
    """Return True if the entry was published within the last _MAX_AGE_DAYS days."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published is None:
        return True  # No date info — don't filter out
    published_dt = datetime(*published[:6], tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - published_dt
    return age.days <= _MAX_AGE_DAYS


def _parse_feed(url: str, limit: int) -> list[dict[str, str]]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        if not _is_recent(entry):
            continue
        raw_summary = entry.get("summary", entry.get("description", ""))
        summary_text = _clean_summary(raw_summary)
        image_url = _extract_image_url(entry)

        article_data: dict[str, str] = {
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "summary": _truncate_at_sentence(summary_text, 300) if summary_text else "",
        }

        # Only add image_url if it exists
        if image_url:
            article_data["image_url"] = image_url

        items.append(article_data)
        if len(items) >= limit:
            break
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
