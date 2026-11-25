"""Date, timezone, and free-slot helpers for Asia/Jerusalem Google Calendar tools."""

from __future__ import annotations

from datetime import date as date_cls, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

TIMEZONE_NAME = "Asia/Jerusalem"
JERUSALEM_TZ = ZoneInfo(TIMEZONE_NAME)
WORK_START_HOUR = 8
WORK_END_HOUR = 20


def parse_dt(value: str) -> datetime:
    """Parse an ISO 8601 datetime string, defaulting naive values to Asia/Jerusalem."""
    dt = datetime.fromisoformat(value.strip())
    if dt.tzinfo is None:
        return dt.replace(tzinfo=JERUSALEM_TZ)
    return dt.astimezone(JERUSALEM_TZ)


def event_bounds(event: dict[str, Any]) -> tuple[datetime, datetime] | None:
    """Return (start, end) in Asia/Jerusalem for busy events, or None if free/cancelled."""
    if event.get("status") == "cancelled" or event.get("transparency") == "transparent":
        return None
    start_info = event.get("start", {})
    end_info = event.get("end", {})
    if "dateTime" in start_info and "dateTime" in end_info:
        return parse_dt(start_info["dateTime"]), parse_dt(end_info["dateTime"])
    if "date" in start_info and "date" in end_info:
        start_d = date_cls.fromisoformat(start_info["date"])
        end_d = date_cls.fromisoformat(end_info["date"])
        return (
            datetime.combine(start_d, time.min, tzinfo=JERUSALEM_TZ),
            datetime.combine(end_d, time.min, tzinfo=JERUSALEM_TZ),
        )
    return None


def format_event(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Google Calendar event dict into a compact response shape."""
    start_info = event.get("start", {})
    end_info = event.get("end", {})
    return {
        "id": event.get("id", ""),
        "title": event.get("summary", ""),
        "start": start_info.get("dateTime") or start_info.get("date", ""),
        "end": end_info.get("dateTime") or end_info.get("date", ""),
        "location": event.get("location", ""),
        "description": event.get("description", ""),
        "status": event.get("status", ""),
        "html_link": event.get("htmlLink", ""),
    }


def compute_free_slots(
    items: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
    duration_minutes: int,
) -> list[dict[str, Any]]:
    """Compute merged busy intervals and return free gaps >= duration_minutes."""
    busy: list[tuple[datetime, datetime]] = []
    for ev in items:
        bounds = event_bounds(ev)
        if not bounds:
            continue
        s, e = max(bounds[0], window_start), min(bounds[1], window_end)
        if e > s:
            busy.append((s, e))

    busy.sort(key=lambda interval: interval[0])
    merged: list[tuple[datetime, datetime]] = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    required = timedelta(minutes=duration_minutes)
    slots: list[dict[str, Any]] = []
    cursor = window_start
    for s, e in [*merged, (window_end, window_end)]:
        if s - cursor >= required:
            slots.append(
                {
                    "start": cursor.isoformat(),
                    "end": s.isoformat(),
                    "duration_minutes": int((s - cursor).total_seconds() // 60),
                }
            )
        cursor = max(cursor, e)
    return slots
