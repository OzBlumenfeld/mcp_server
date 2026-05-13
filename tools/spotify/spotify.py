"""Spotify tools: top tracks and top podcasts by recent play frequency."""

import base64
import os
from collections import Counter
from typing import Any

import httpx

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"


def _get_access_token() -> str:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID, "
            "SPOTIFY_CLIENT_SECRET, and SPOTIFY_REFRESH_TOKEN in .env"
        )

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            _TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
    return str(resp.json()["access_token"])


def get_top_tracks(limit: int = 5) -> list[dict[str, Any]]:
    """
    Fetch the user's top tracks over the last ~4 weeks (Spotify's shortest window).
    Requires the user-top-read OAuth scope.
    """
    token = _get_access_token()
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{_API_BASE}/me/top/tracks",
            headers={"Authorization": f"Bearer {token}"},
            params={"time_range": "short_term", "limit": limit},
        )
        resp.raise_for_status()
    items: list[dict[str, Any]] = resp.json().get("items", [])
    return [
        {
            "rank": i + 1,
            "title": track["name"],
            "artists": ", ".join(a["name"] for a in track["artists"]),
            "album": track["album"]["name"],
            "popularity": track["popularity"],
            "url": track["external_urls"].get("spotify"),
        }
        for i, track in enumerate(items)
    ]


def get_top_podcasts(limit: int = 5) -> list[dict[str, Any]]:
    """
    Derive the user's top podcasts by counting episode plays in the last 50
    recently-played items, then ranking shows by frequency.
    Requires the user-read-recently-played OAuth scope.
    """
    token = _get_access_token()
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{_API_BASE}/me/player/recently-played",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 50},
        )
        resp.raise_for_status()
    items: list[dict[str, Any]] = resp.json().get("items", [])

    # Filter to episode type items and count plays per show
    show_counts: Counter[str] = Counter()
    show_meta: dict[str, dict[str, Any]] = {}

    for item in items:
        track = item.get("track", {})
        if track.get("type") != "episode":
            continue
        show = track.get("show", {})
        show_id = show.get("id")
        if not show_id:
            continue
        show_counts[show_id] += 1
        if show_id not in show_meta:
            show_meta[show_id] = {
                "name": show.get("name", "Unknown"),
                "publisher": show.get("publisher", "Unknown"),
                "url": (show.get("external_urls") or {}).get("spotify"),
            }

    top = show_counts.most_common(limit)
    return [
        {
            "rank": i + 1,
            "name": show_meta[show_id]["name"],
            "publisher": show_meta[show_id]["publisher"],
            "recent_plays": count,
            "url": show_meta[show_id]["url"],
        }
        for i, (show_id, count) in enumerate(top)
    ]
