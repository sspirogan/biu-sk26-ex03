# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "google-auth-oauthlib>=1.2.0",
# ]
# ///
"""One-time standalone OAuth authorization helper (never imported by the MCP server).

Reuses the existing Google client_secret*.json in GOOGLE_PRIVATE_DIR (default:
/Users/pirogan4ik/Desktop/private), backs up any existing token.json in that
same private folder, runs a local browser OAuth consent flow to grant
gmail.readonly alongside gmail.compose and calendar.events, and saves the
updated token.json back to the private folder without printing secrets.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil

from google_auth_oauthlib.flow import InstalledAppFlow

DEFAULT_PRIVATE_DIR = Path("/Users/pirogan4ik/Desktop/private")
REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.events",
]


def _find_client_secret(private_dir: Path) -> Path:
    matches = sorted(private_dir.glob("client_secret*.json"))
    if not matches:
        raise FileNotFoundError(f"No client_secret*.json file found in {private_dir}")
    return matches[0]


def _read_existing_scopes(token_file: Path) -> list[str]:
    if not token_file.is_file():
        return []
    data = json.loads(token_file.read_text(encoding="utf-8"))
    raw_scopes = data.get("scopes")
    if isinstance(raw_scopes, list):
        return [str(s) for s in raw_scopes if s]
    raw_scope = data.get("scope")
    if isinstance(raw_scope, str):
        return [s for s in raw_scope.split() if s]
    return []


def _merge_scopes(existing: list[str], required: list[str]) -> list[str]:
    merged: list[str] = []
    for scope in [*existing, *required]:
        if scope not in merged:
            merged.append(scope)
    return merged


def _backup_token(token_file: Path) -> Path | None:
    if not token_file.is_file():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = token_file.with_name(f"token.json.bak.{timestamp}")
    shutil.copy2(token_file, backup_file)
    os.chmod(backup_file, 0o600)
    return backup_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time OAuth authorization to add gmail.readonly to token.json."
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path(os.environ.get("GOOGLE_PRIVATE_DIR", str(DEFAULT_PRIVATE_DIR))),
        help=f"Directory containing client_secret*.json and token.json (default: {DEFAULT_PRIVATE_DIR})",
    )
    args = parser.parse_args()

    private_dir = args.private_dir.expanduser().resolve()
    if not private_dir.is_dir():
        raise FileNotFoundError(f"Private directory does not exist: {private_dir}")

    client_file = _find_client_secret(private_dir)
    token_file = private_dir / "token.json"

    existing_scopes = _read_existing_scopes(token_file)
    target_scopes = _merge_scopes(existing_scopes, REQUIRED_SCOPES)

    print(f"Using client file: {client_file.name} (in {private_dir})")
    print("Existing scopes:", existing_scopes or ["<none>"])
    print("Requesting scopes:", target_scopes)
    print("Opening browser for Google OAuth consent...")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes=target_scopes)
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    backup_file = _backup_token(token_file)
    if backup_file is not None:
        print(f"Backed up previous token to: {backup_file}")

    token_file.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_file, 0o600)

    granted_scopes = sorted(creds.scopes or target_scopes)
    print(f"Saved new token to: {token_file}")
    print("Granted scopes:", granted_scopes)
    print("Has refresh_token:", bool(creds.refresh_token))


if __name__ == "__main__":
    main()
