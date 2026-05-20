"""Weekly calendar summary script: fetch events for the next 7 days and email to self."""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

if os.getenv("ENV", "local") == "local":
    load_dotenv(Path(__file__).parent.parent.parent / ".env")

from email_sender import EmailNotificationSender
from tools.calendar.calendar import fetch_calendar_events


def get_recipient() -> str:
    email = os.getenv("GMAIL_SENDER_EMAIL")
    if not email:
        raise ValueError("GMAIL_SENDER_EMAIL environment variable not set.")
    return email


def _event_card_html(event: dict[str, Any]) -> str:
    title = event.get("title", "No title")
    time_str = event.get("time", "")
    location = event.get("location", "")
    description = event.get("description", "")

    location_html = (
        f'<div style="color:#6b7280;font-size:13px;margin-top:4px;">📍 {location}</div>'
        if location else ""
    )
    description_html = (
        f'<div style="color:#555;font-size:13px;margin-top:6px;line-height:1.5;">{description}</div>'
        if description else ""
    )

    return f"""
    <div style="margin:10px 0;padding:12px 15px;background:#fff;border-left:4px solid #667eea;
                border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:4px;">
            <div style="font-weight:600;color:#1f2937;font-size:15px;">{title}</div>
            <div style="font-size:13px;color:#667eea;white-space:nowrap;">🕐 {time_str}</div>
        </div>
        {location_html}
        {description_html}
    </div>
    """


def _day_section_html(day: dict[str, Any]) -> str:
    label = day["label"]
    events: list[dict[str, Any]] = day["events"]

    if not events:
        events_html = '<div style="color:#9ca3af;font-size:14px;padding:10px 0;">No events</div>'
    else:
        events_html = "".join(_event_card_html(e) for e in events)

    count_badge = (
        f'<span style="background:#667eea;color:#fff;border-radius:12px;'
        f'padding:2px 10px;font-size:12px;font-weight:600;">'
        f'{len(events)} event{"s" if len(events) != 1 else ""}</span>'
    )

    return f"""
    <div style="margin:24px 0;">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:12px 16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                    border-radius:10px;margin-bottom:12px;">
            <h3 style="color:#fff;margin:0;font-size:18px;font-weight:700;">{label}</h3>
            {count_badge}
        </div>
        {events_html}
    </div>
    """


def create_calendar_email_html(calendar_data: dict[str, Any]) -> str:
    range_start = calendar_data["range_start"]
    range_end = calendar_data["range_end"]
    days: list[dict[str, Any]] = calendar_data["days"]

    total_events = sum(len(d["events"]) for d in days)
    days_html = "".join(_day_section_html(d) for d in days)
    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Calendar Summary</title>
    </head>
    <body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#f5f5f5;">
        <div style="max-width:700px;margin:0 auto;background:#fff;">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:40px 20px;text-align:center;">
                <h1 style="color:#fff;margin:0;font-size:30px;font-weight:700;">📅 WEEKLY CALENDAR</h1>
                <p style="color:rgba(255,255,255,0.9);margin:10px 0 0;font-size:16px;">
                    {range_start} – {range_end}
                </p>
                <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:14px;">
                    {total_events} event{"s" if total_events != 1 else ""} coming up
                </p>
            </div>

            <!-- Content -->
            <div style="padding:24px 20px;">
                {days_html}
            </div>

            <!-- Footer -->
            <div style="background:#f8f9fa;padding:24px 20px;text-align:center;border-top:1px solid #e5e7eb;">
                <p style="color:#6b7280;font-size:13px;margin:0 0 6px;">
                    📧 Weekly calendar summary — automatically generated.
                </p>
                <p style="color:#9ca3af;font-size:12px;margin:0;">Generated on {generated_at} UTC</p>
            </div>
        </div>
    </body>
    </html>
    """


async def send_weekly_calendar_email() -> None:
    recipient = get_recipient()

    now = datetime.now(timezone.utc)
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"📅 Fetching calendar events from {start_date} to {end_date}...")
    calendar_data = fetch_calendar_events(start_date=start_date, end_date=end_date)

    total = sum(len(d["events"]) for d in calendar_data["days"])
    print(f"   Found {total} events")

    print("✍️  Formatting email...")
    html_body = create_calendar_email_html(calendar_data)
    plain_body = (
        f"Weekly Calendar Summary\n"
        f"{calendar_data['range_start']} – {calendar_data['range_end']}\n\n"
        "Please view this email in an HTML-capable email client for the full summary."
    )

    subject = f"📅 Weekly Calendar — {calendar_data['range_start']}"

    email_sender = EmailNotificationSender()
    print(f"📨 Sending to {recipient}...")

    success = await email_sender.send_email(recipient, subject, plain_body, html_body=html_body)
    print(f"   {'✅' if success else '❌'} {recipient}")
    print(f"\n✨ {'Sent successfully' if success else 'Failed to send'}")


if __name__ == "__main__":
    asyncio.run(send_weekly_calendar_email())
