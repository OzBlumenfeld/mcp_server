"""
One-time script to obtain a Spotify refresh token.

Usage:
    uv run tools/spotify/get_refresh_token.py

Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env (or env).
Prints the refresh token to copy into your .env file.

Setup:
    In Spotify Developer Dashboard → your app → Edit Settings,
    add this Redirect URI: http://127.0.0.1:8888/callback
"""

import base64
import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from dotenv import load_dotenv

load_dotenv()

_REDIRECT_URI = "http://127.0.0.1:8888/callback"
_SCOPES = "user-top-read user-read-recently-played"
_AUTH_URL = "https://accounts.spotify.com/authorize"
_TOKEN_URL = "https://accounts.spotify.com/api/token"

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
    })
    return f"{_AUTH_URL}?{params}"


def _exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, str]:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            _TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _REDIRECT_URI,
            },
        )
        resp.raise_for_status()
    return dict(resp.json())


def main() -> None:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file first.")

    auth_url = _build_auth_url(client_id)
    print("Opening Spotify authorization in your browser...")
    webbrowser.open(auth_url)

    print("Waiting for Spotify to redirect to 127.0.0.1:8888 ...")
    server = HTTPServer(("127.0.0.1", 8888), _CallbackHandler)
    server.handle_request()

    if not _auth_code:
        raise SystemExit("No authorization code received.")

    tokens = _exchange_code(client_id, client_secret, _auth_code)
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise SystemExit(f"No refresh token in response: {tokens}")

    print("\nSuccess! Add this to your .env file:")
    print(f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}\n")


if __name__ == "__main__":
    main()
