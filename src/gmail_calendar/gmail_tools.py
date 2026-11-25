"""Read-only Gmail search/read helpers and draft creation (never sends or deletes)."""

from __future__ import annotations

import base64
from email.message import EmailMessage
import re
from typing import Any


def _header_map(headers: list[dict[str, str]]) -> dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in headers}


def _decode_b64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")


def _extract_body(payload: dict[str, Any]) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            text = _decode_b64url(data)
            if mime_type == "text/plain":
                plain_parts.append(text)
            elif mime_type == "text/html":
                html_parts.append(text)
        for child in part.get("parts", []):
            walk(child)

    walk(payload)
    if plain_parts:
        return "\n".join(plain_parts).strip()
    if html_parts:
        raw_html = "\n".join(html_parts)
        return re.sub(r"<[^>]+>", " ", raw_html).strip()
    return ""


def search_emails(service: Any, query: str, max_results: int = 10) -> dict[str, Any]:
    """Search Gmail messages matching a query without modifying mailbox state."""
    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100.")

    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    items: list[dict[str, str]] = []
    for ref in response.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )
        headers = _header_map(msg.get("payload", {}).get("headers", []))
        items.append(
            {
                "id": msg.get("id", ""),
                "thread_id": msg.get("threadId", ""),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "snippet": msg.get("snippet", ""),
            }
        )
    return {"query": query, "count": len(items), "emails": items}


def read_email(service: Any, message_id: str) -> dict[str, Any]:
    """Read a full Gmail message by ID."""
    clean_id = message_id.strip()
    if not clean_id:
        raise ValueError("message_id must not be empty.")

    msg = service.users().messages().get(userId="me", id=clean_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = _header_map(payload.get("headers", []))
    return {
        "id": msg.get("id", ""),
        "thread_id": msg.get("threadId", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "body": _extract_body(payload),
        "labels": msg.get("labelIds", []),
    }


def create_draft(service: Any, to: str, subject: str, body: str) -> dict[str, Any]:
    """Create a Gmail draft only; never sends the message."""
    recipient = to.strip()
    if not recipient:
        raise ValueError("to must not be empty.")

    email_msg = EmailMessage()
    email_msg["To"] = recipient
    email_msg["Subject"] = subject
    email_msg.set_content(body)

    encoded = base64.urlsafe_b64encode(email_msg.as_bytes()).decode("ascii")
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": encoded}})
        .execute()
    )
    return {
        "status": "draft_created",
        "draft_id": draft.get("id", ""),
        "message_id": draft.get("message", {}).get("id", ""),
        "to": recipient,
        "subject": subject,
    }
