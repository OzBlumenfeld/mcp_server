"""Daily newsletter script: fetch summary and email to subscribers."""

import asyncio
import os
import re
from datetime import datetime
from html import unescape
from typing import Any

from email_sender import EmailNotificationSender
from tools.daily_summary import get_daily_summary


MAX_SUBSCRIBERS = 5


def get_subscribers() -> list[str]:
    """
    Get newsletter subscribers from environment variable.

    Expects NEWSLETTER_SUBSCRIBERS env var with comma-separated emails.
    Example: "email1@example.com,email2@example.com,email3@example.com"

    Returns:
        List of subscriber email addresses
    """
    subscribers_env = os.getenv("NEWSLETTER_SUBSCRIBERS", "")

    if not subscribers_env:
        raise ValueError(
            "NEWSLETTER_SUBSCRIBERS environment variable not set. "
            "Please set it to a comma-separated list of email addresses."
        )

    # Split by comma and strip whitespace
    subscribers = [email.strip() for email in subscribers_env.split(",")]

    # Filter out empty strings
    subscribers = [email for email in subscribers if email]

    # Validate email format (basic check)
    invalid_emails = [email for email in subscribers if "@" not in email or "." not in email]
    if invalid_emails:
        raise ValueError(f"Invalid email addresses found: {', '.join(invalid_emails)}")

    return subscribers


NEWSLETTER_SUBSCRIBERS = get_subscribers()


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities from text."""
    # Remove HTML tags (including self-closing tags like <img />)
    text = re.sub(r'<[^>]+/?>', '', text)
    # Decode HTML entities (e.g., &amp; -> &)
    text = unescape(text)
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_news_section_html(title: str, emoji: str, news_data: list[dict[str, Any]]) -> str:
    """Format a news section with HTML styling."""
    section = f"""
    <div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px;">
        <h2 style="color: white; margin: 0; font-size: 24px; font-weight: bold;">
            {emoji} {title}
        </h2>
    </div>
    """

    for source_data in news_data:
        source_name = source_data["source"]
        articles = source_data["articles"]

        section += f"""
        <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 8px;">
            <h3 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">
                📰 {source_name}
            </h3>
        """

        for idx, article in enumerate(articles, 1):
            title_text = clean_html(article.get("title", "No title"))
            summary_text = clean_html(article.get("summary", ""))
            link = article.get("link", "")

            section += f"""
            <div style="margin: 15px 0; padding: 12px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight: bold; color: #2c3e50; margin-bottom: 8px; font-size: 16px;">
                    {idx}. {title_text}
                </div>
            """

            if summary_text and len(summary_text) > 0:
                section += f"""
                <div style="color: #555; margin: 8px 0; font-size: 14px; line-height: 1.6;">
                    {summary_text}
                </div>
                """

            if link:
                section += f"""
                <div style="margin-top: 8px;">
                    <a href="{link}" style="color: #667eea; text-decoration: none; font-size: 14px; font-weight: 500;">
                        🔗 Read more →
                    </a>
                </div>
                """

            section += "</div>"

        section += "</div>"

    return section


def format_market_section_html(market_data: list[dict[str, Any]]) -> str:
    """Format the market data section with HTML styling."""
    section = """
    <div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 12px;">
        <h2 style="color: white; margin: 0; font-size: 24px; font-weight: bold;">
            📈 MARKET SNAPSHOT
        </h2>
        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">
            Daily & Weekly Performance
        </p>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin: 20px 0;">
    """

    for item in market_data:
        if "error" in item:
            section += f"""
            <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 8px;">
                <div style="font-weight: bold; color: #856404;">
                    ❌ {item['symbol']}: Error
                </div>
                <div style="font-size: 12px; color: #856404; margin-top: 5px;">
                    {item['error']}
                </div>
            </div>
            """
        else:
            symbol = item.get("symbol", "N/A")
            price = item.get("current_price", "N/A")
            daily_change_pct = item.get("daily_change_pct", None)
            weekly_change_pct = item.get("weekly_change_pct", None)

            # Determine color and emoji based on weekly performance
            if weekly_change_pct is not None:
                if weekly_change_pct > 0:
                    emoji = "📈"
                    color = "#10b981"
                    bg_color = "#d1fae5"
                elif weekly_change_pct < 0:
                    emoji = "📉"
                    color = "#ef4444"
                    bg_color = "#fee2e2"
                else:
                    emoji = "➖"
                    color = "#6b7280"
                    bg_color = "#f3f4f6"
            else:
                emoji = "➖"
                color = "#6b7280"
                bg_color = "#f3f4f6"

            section += f"""
            <div style="padding: 15px; background-color: {bg_color}; border-left: 4px solid {color}; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 20px; font-weight: bold; color: #1f2937;">
                        {emoji} {symbol}
                    </div>
                    <div style="font-size: 24px; font-weight: bold; color: {color};">
                        ${price}
                    </div>
                </div>
                <div style="display: flex; gap: 15px; font-size: 13px;">
            """

            # Daily change
            if daily_change_pct is not None:
                daily_color = "#10b981" if daily_change_pct > 0 else "#ef4444" if daily_change_pct < 0 else "#6b7280"
                section += f"""
                    <div style="flex: 1;">
                        <div style="color: #6b7280; font-size: 11px; text-transform: uppercase;">Today</div>
                        <div style="font-weight: bold; color: {daily_color}; font-size: 15px;">
                            {daily_change_pct:+.2f}%
                        </div>
                    </div>
                """
            else:
                section += """
                    <div style="flex: 1;">
                        <div style="color: #6b7280; font-size: 11px; text-transform: uppercase;">Today</div>
                        <div style="color: #9ca3af;">N/A</div>
                    </div>
                """

            # Weekly change
            if weekly_change_pct is not None:
                section += f"""
                    <div style="flex: 1;">
                        <div style="color: #6b7280; font-size: 11px; text-transform: uppercase;">This Week</div>
                        <div style="font-weight: bold; color: {color}; font-size: 15px;">
                            {weekly_change_pct:+.2f}%
                        </div>
                    </div>
                """
            else:
                section += """
                    <div style="flex: 1;">
                        <div style="color: #6b7280; font-size: 11px; text-transform: uppercase;">This Week</div>
                        <div style="color: #9ca3af;">N/A</div>
                    </div>
                """

            section += """
                </div>
            </div>
            """

    section += "</div>"
    return section


def create_newsletter_body_html(summary_data: dict[str, Any]) -> str:
    """Create the complete newsletter email body with HTML styling."""
    today = datetime.now().strftime("%B %d, %Y")

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Newsletter - {today}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 32px; font-weight: bold;">
                    🌅 DAILY NEWSLETTER
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">
                    {today}
                </p>
            </div>

            <!-- Content -->
            <div style="padding: 20px;">
                <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Good morning! ☀️ Here's your daily digest of news and market updates.
                </p>
    """

    # Add market data section FIRST
    if "market_data" in summary_data:
        body += format_market_section_html(summary_data["market_data"])

    # Add Israeli news section
    if "israeli_news" in summary_data:
        body += format_news_section_html("ISRAELI NEWS", "🇮🇱", summary_data["israeli_news"])

    # Add world news section
    if "world_news" in summary_data:
        body += format_news_section_html("WORLD NEWS", "🌍", summary_data["world_news"])

    # Add tech news section
    if "tech_news" in summary_data:
        body += format_news_section_html("TECH NEWS", "💻", summary_data["tech_news"])

    body += """
            </div>

            <!-- Footer -->
            <div style="background-color: #f8f9fa; padding: 30px 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px; margin: 0 0 10px 0;">
                    📧 This newsletter was automatically generated and delivered to you.
                </p>
                <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                    To unsubscribe, please reply to this email.
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    return body


async def send_newsletter() -> None:
    """Fetch daily summary and send newsletter to all subscribers."""
    # Safety check: Prevent sending to too many subscribers
    if len(NEWSLETTER_SUBSCRIBERS) > MAX_SUBSCRIBERS:
        raise ValueError(
            f"Subscriber count ({len(NEWSLETTER_SUBSCRIBERS)}) exceeds maximum allowed ({MAX_SUBSCRIBERS}). "
            f"Increase MAX_SUBSCRIBERS if this is intentional."
        )

    print("📧 Fetching daily summary...")
    summary_data = get_daily_summary(news_limit=5)

    print("✍️  Formatting newsletter...")
    newsletter_html = create_newsletter_body_html(summary_data)

    # Create a simple plain text version as fallback
    today = datetime.now().strftime("%B %d, %Y")
    newsletter_plain = f"Daily Newsletter - {today}\n\nPlease view this email in an HTML-capable email client for the best experience."

    subject = f"📰 Daily Newsletter - {today}"

    print(f"📨 Sending newsletter to {len(NEWSLETTER_SUBSCRIBERS)} subscriber(s)...")

    # Initialize email sender
    email_sender = EmailNotificationSender()

    # Send to all subscribers
    success_count = 0
    for subscriber in NEWSLETTER_SUBSCRIBERS:
        print(f"   Sending to {subscriber}...")
        success = await email_sender.send_email(subscriber, subject, newsletter_plain, html_body=newsletter_html)
        if success:
            print(f"   ✅ Sent to {subscriber}")
            success_count += 1
        else:
            print(f"   ❌ Failed to send to {subscriber}")

    print(f"\n✨ Newsletter sent successfully to {success_count}/{len(NEWSLETTER_SUBSCRIBERS)} subscriber(s)")


if __name__ == "__main__":
    asyncio.run(send_newsletter())