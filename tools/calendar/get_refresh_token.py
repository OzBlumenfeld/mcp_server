"""
One-time script to obtain a Google Calendar refresh token.

Usage:
    uv run tools/calendar/get_refresh_token.py

Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env (or env).
Prints the refresh token to copy into your .env file.

Setup:
    In Google Cloud Console → APIs & Services → Credentials → your OAuth
    2.0 Client ID (Desktop or Web app type), add this Authorized redirect
    URI: http://127.0.0.1:8888/callback
    Also make sure the Google Calendar API is enabled for the project,
    and that your Google account is added as a test user if the OAuth
    consent screen is in "Testing" status.
"""

import asyncio
import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from dotenv import load_dotenv
from oz_shared import load_op_secrets

load_dotenv()

_REDIRECT_URI = "http://127.0.0.1:8888/callback"
_SCOPES = "https://www.googleapis.com/auth/calendar.readonly"
_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"

_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization denied.")
            return

        _auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authorization successful! You can close this tab.")

    def log_message(self, _format: str, *_args: object) -> None:
        pass  # suppress request logs


def _build_auth_url(client_id: str) -> str:
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": _REDIRECT_URI,
        "scope": _SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"{_AUTH_URL}?{params}"


def _exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, str]:
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            _TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": _REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
    return dict(resp.json())


def main() -> None:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file first.")

    auth_url = _build_auth_url(client_id)
    print("Opening Google authorization in your browser...")
    webbrowser.open(auth_url)

    print("Waiting for Google to redirect to 127.0.0.1:8888 ...")
    server = HTTPServer(("127.0.0.1", 8888), _CallbackHandler)
    server.handle_request()

    if not _auth_code:
        raise SystemExit("No authorization code received.")

    tokens = _exchange_code(client_id, client_secret, _auth_code)
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise SystemExit(
            f"No refresh token in response: {tokens}\n"
            "If you've authorized this app before, revoke access at "
            "https://myaccount.google.com/permissions and try again "
            "(Google only returns a refresh token on first consent, or "
            "when access_type=offline + prompt=consent forces re-consent)."
        )

    print("\nSuccess! Add this to your .env file:")
    print(f"\nGOOGLE_CALENDAR_REFRESH_TOKEN={refresh_token}\n")


if __name__ == "__main__":
    asyncio.run(load_op_secrets())
    main()
