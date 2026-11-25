"""FastMCP (MCPServer) stdio server for Gmail and Google Calendar."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from gmail_calendar.auth import get_calendar_service, get_gmail_service
from gmail_calendar.calendar_tools import (
    create_event as create_calendar_event,
    find_free_slots as find_calendar_free_slots,
    list_events as list_calendar_events,
)
from gmail_calendar.gmail_tools import (
    create_draft as create_gmail_draft,
    read_email as read_gmail_message,
    search_emails as search_gmail_messages,
)

mcp = MCPServer("gmail-calendar")


@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> dict[str, Any]:
    """Search Gmail messages using standard Gmail query syntax without modifying mail."""
    return search_gmail_messages(get_gmail_service(), query=query, max_results=max_results)


@mcp.tool()
def read_email(message_id: str) -> dict[str, Any]:
    """Read the headers and body of a single Gmail message by its message ID."""
    return read_gmail_message(get_gmail_service(), message_id=message_id)


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> dict[str, Any]:
    """Create an email draft in Gmail only; never sends the message."""
    return create_gmail_draft(get_gmail_service(), to=to, subject=subject, body=body)


@mcp.tool()
def list_events(days_ahead: int = 7) -> dict[str, Any]:
    """List upcoming Google Calendar events for the next N days in Asia/Jerusalem."""
    return list_calendar_events(get_calendar_service(), days_ahead=days_ahead)


@mcp.tool()
def find_free_slots(date: str, duration_minutes: int = 30) -> dict[str, Any]:
    """Find available calendar slots on YYYY-MM-DD (08:00-20:00 Asia/Jerusalem)."""
    return find_calendar_free_slots(
        get_calendar_service(), date=date, duration_minutes=duration_minutes
    )


@mcp.tool()
def create_event(
    title: str, start: str, end: str, description: str = ""
) -> dict[str, Any]:
    """Create a Google Calendar event using ISO 8601 start/end times in Asia/Jerusalem."""
    return create_calendar_event(
        get_calendar_service(),
        title=title,
        start=start,
        end=end,
        description=description,
    )


def main() -> None:
    """Run the gmail-calendar MCP server over stdio."""
    mcp.run(transport="stdio")
