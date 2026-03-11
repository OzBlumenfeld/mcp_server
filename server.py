import logging
import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

from email_sender import EmailNotificationSender
from logging_config import setup_logging
from tools.finance import get_etf_price, get_market_snapshot
from tools.news import get_israeli_news, get_tech_news
from tools.strava import get_recent_activities, get_weekly_summary

# Load environment variables from .env file
load_dotenv()

# Call setup_logging at the top level
setup_logging()

logger = logging.getLogger(__name__)


mcp = FastMCP(
    name="MyAssistantServer",
    instructions=(
        "This server provides tools for math, email notifications, "
        "news (NewsAPI + RSS), finance (Yahoo Finance), and Strava fitness data."
    ),
)


# ── Math ──────────────────────────────────────────────────────────────────────

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    return a * b


# ── Email ─────────────────────────────────────────────────────────────────────

@mcp.tool
async def send_email(recipient_email: str, subject: str, body: str) -> str:
    """Send an email via Gmail SMTP."""
    logger.info(
        "Send email called",
        extra={"recipient_email": recipient_email, "subject": subject},
    )
    email_sender = EmailNotificationSender()
    success = await email_sender.send_email(
        recipient_email=recipient_email, subject=subject, body=body
    )
    if success:
        return f"Email sent successfully to {recipient_email}."
    return f"Failed to send email to {recipient_email}. Please check the server logs."


# ── News (NewsAPI) ────────────────────────────────────────────────────────────

@mcp.tool
async def fetch_news(query: str | None = None, category: str | None = None) -> str:
    """
    Fetch top 20 news headlines from NewsAPI.
    Categories: business, entertainment, general, health, science, sports, technology.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key or api_key == "your_news_api_key_here":
        return "Error: NEWS_API_KEY not configured. Add it to your .env file."

    base_url = "https://newsapi.org/v2/top-headlines"
    params: dict[str, str | int] = {
        "apiKey": api_key,
        "pageSize": 20,
        "language": "en",
    }
    if query:
        params["q"] = query
    if category:
        params["category"] = category

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            if not articles:
                return f"No news found for query: {query}" if query else "No top headlines found."
            lines = ["Latest News Headlines:"]
            for i, article in enumerate(articles, 1):
                title = article.get("title")
                source = article.get("source", {}).get("name")
                url = article.get("url")
                lines.append(f"{i}. {title} (Source: {source}) - {url}")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return f"Failed to fetch news: {str(e)}"


# ── News (RSS) ────────────────────────────────────────────────────────────────

mcp.tool(get_israeli_news)
mcp.tool(get_tech_news)

# ── Finance ───────────────────────────────────────────────────────────────────

mcp.tool(get_etf_price)
mcp.tool(get_market_snapshot)

# ── Strava ────────────────────────────────────────────────────────────────────

mcp.tool(get_recent_activities)
mcp.tool(get_weekly_summary)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", port=9005)
