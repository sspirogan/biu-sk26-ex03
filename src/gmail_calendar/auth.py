"""Google OAuth credential loading without browser interaction or secret logging."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ENV_VAR = "GOOGLE_PRIVATE_DIR"
_cached_creds: Credentials | None = None


def _get_private_dir() -> Path:
    raw = os.environ.get(ENV_VAR, "").strip()
    if not raw:
        raise RuntimeError(f"Environment variable {ENV_VAR} is not set.")
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise FileNotFoundError(f"{ENV_VAR} directory does not exist: {path}")
    return path


def _find_client_secret(private_dir: Path) -> Path:
    matches = sorted(private_dir.glob("client_secret*.json"))
    if not matches:
        raise FileNotFoundError(f"No client_secret*.json file found in {private_dir}")
    return matches[0]


def _load_client_fallback(client_file: Path) -> tuple[str | None, str | None, str | None]:
    data = json.loads(client_file.read_text(encoding="utf-8"))
    section = data.get("installed") or data.get("web") or {}
    return section.get("client_id"), section.get("client_secret"), section.get("token_uri")


def load_credentials() -> Credentials:
    """Load and refresh Google credentials from GOOGLE_PRIVATE_DIR in memory."""
    global _cached_creds

    if _cached_creds is not None:
        if _cached_creds.expired and _cached_creds.refresh_token:
            _cached_creds.refresh(Request())
        if _cached_creds.valid:
            return _cached_creds

    private_dir = _get_private_dir()
    client_file = _find_client_secret(private_dir)
    token_file = private_dir / "token.json"
    if not token_file.is_file():
        raise FileNotFoundError(f"token.json not found in {private_dir}")

    creds = Credentials.from_authorized_user_file(str(token_file))
    if not creds.client_id or not creds.client_secret:
        client_id, client_secret, token_uri = _load_client_fallback(client_file)
        creds = Credentials(
            token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri or token_uri or "https://oauth2.googleapis.com/token",
            client_id=creds.client_id or client_id,
            client_secret=creds.client_secret or client_secret,
            scopes=creds.scopes,
        )

    if creds.expired:
        if not creds.refresh_token:
            raise RuntimeError("Stored Google token is expired and has no refresh token.")
        creds.refresh(Request())

    if not creds.valid:
        raise RuntimeError("Stored Google credentials are invalid.")

    _cached_creds = creds
    return creds


def get_gmail_service() -> Any:
    """Build an authenticated Gmail API v1 client."""
    return build("gmail", "v1", credentials=load_credentials(), cache_discovery=False)


def get_calendar_service() -> Any:
    """Build an authenticated Google Calendar API v3 client."""
    return build("calendar", "v3", credentials=load_credentials(), cache_discovery=False)
