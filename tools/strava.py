"""Strava tools: activity summary and weekly training load."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

_TOKEN_URL = "https://www.strava.com/oauth/token"
_API_BASE = "https://www.strava.com/api/v3"


def _get_access_token() -> str:
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing Strava credentials. Set STRAVA_CLIENT_ID, "
            "STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN in .env"
        )

    with httpx.Client(timeout=10) as client:
        resp = client.post(
            _TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
    return str(resp.json()["access_token"])


def _meters_to_km(meters: float) -> float:
    return round(meters / 1000, 2)


def _seconds_to_hms(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_recent_activities(limit: int = 5) -> list[dict[str, Any]]:
    """Fetch the most recent Strava activities with key stats."""
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{_API_BASE}/athlete/activities",
            headers=headers,
            params={"per_page": limit},
        )
        resp.raise_for_status()
    activities = resp.json()
    return [
        {
            "name": a["name"],
            "type": a["type"],
            "date": a["start_date_local"][:10],
            "distance_km": _meters_to_km(a.get("distance", 0)),
            "duration": _seconds_to_hms(a.get("moving_time", 0)),
            "elevation_m": round(a.get("total_elevation_gain", 0), 1),
            "average_hr": a.get("average_heartrate"),
            "kudos": a.get("kudos_count", 0),
        }
        for a in activities
    ]


def get_weekly_summary() -> dict[str, Any]:
    """Get a training load summary for the current week (Mon–today)."""
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    after_ts = int(monday.replace(hour=0, minute=0, second=0).timestamp())

    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{_API_BASE}/athlete/activities",
            headers=headers,
            params={"after": after_ts, "per_page": 50},
        )
        resp.raise_for_status()
    activities = resp.json()

    total_distance = sum(a.get("distance", 0) for a in activities)
    total_time = sum(a.get("moving_time", 0) for a in activities)
    total_elevation = sum(a.get("total_elevation_gain", 0) for a in activities)
    types: dict[str, int] = {}
    for a in activities:
        t = a.get("type", "Other")
        types[t] = types.get(t, 0) + 1

    return {
        "week_starting": monday.strftime("%Y-%m-%d"),
        "activity_count": len(activities),
        "activity_types": types,
        "total_distance_km": _meters_to_km(total_distance),
        "total_duration": _seconds_to_hms(total_time),
        "total_elevation_m": round(total_elevation, 1),
    }
