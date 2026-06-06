"""Google Calendar tool: fetch calendar events for an arbitrary date range."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _get_access_token() -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing Google credentials. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET, and GOOGLE_CALENDAR_REFRESH_TOKEN in .env"
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


def _format_event_time(start: dict[str, str], end: dict[str, str]) -> str:
    if "dateTime" in start:
        start_dt = datetime.fromisoformat(start["dateTime"])
        end_dt = datetime.fromisoformat(end.get("dateTime", start["dateTime"]))
        return f"{start_dt.strftime('%H:%M')} – {end_dt.strftime('%H:%M')}"
    return "All day"


def fetch_calendar_events(
    start_date: str,
    end_date: str,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """
    Fetch Google Calendar events between two dates and return them grouped by day.

    Args:
        start_date: Start of the range in YYYY-MM-DD format (inclusive, treated as 00:00 UTC).
        end_date:   End of the range in YYYY-MM-DD format (inclusive, treated as 23:59 UTC).
        calendar_id: Google Calendar ID (default: "primary").

    Returns:
        Dict with range labels and a list of day objects, each containing their events.
    """
    token = _get_access_token()

    range_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    range_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{_CALENDAR_API_BASE}/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": range_start.isoformat(),
                "timeMax": range_end.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 250,
            },
        )
        resp.raise_for_status()

    items: list[dict[str, Any]] = resp.json().get("items", [])

    # Build an ordered bucket for every day in the range
    num_days = (range_end.date() - range_start.date()).days + 1
    day_buckets: dict[str, dict[str, Any]] = {}
    for i in range(num_days):
        day_dt = range_start + timedelta(days=i)
        key = day_dt.strftime("%Y-%m-%d")
        weekday_name = _DAY_NAMES[day_dt.weekday()]
        day_buckets[key] = {
            "label": f"{weekday_name}, {day_dt.strftime('%B %d')}",
            "events": [],
        }

    for item in items:
        start = item.get("start", {})
        end = item.get("end", {})
        date_key = start.get("date") or start.get("dateTime", "")[:10]

        if date_key not in day_buckets:
            continue

        day_buckets[date_key]["events"].append({
            "title": item.get("summary", "No title"),
            "time": _format_event_time(start, end),
            "location": item.get("location", ""),
            "description": (item.get("description") or "")[:200],
        })

    return {
        "range_start": range_start.strftime("%B %d, %Y"),
        "range_end": range_end.strftime("%B %d, %Y"),
        "days": [
            {"date": date_key, "label": info["label"], "events": info["events"]}
            for date_key, info in day_buckets.items()
        ],
    }
