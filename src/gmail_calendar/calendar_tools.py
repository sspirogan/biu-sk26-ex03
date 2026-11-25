"""Google Calendar helpers fixed to Asia/Jerusalem (no delete operations)."""

from __future__ import annotations

from datetime import date as date_cls, datetime, time, timedelta
from typing import Any

from gmail_calendar.calendar_helpers import (
    JERUSALEM_TZ,
    TIMEZONE_NAME,
    WORK_END_HOUR,
    WORK_START_HOUR,
    compute_free_slots,
    format_event,
    parse_dt,
)


def list_events(service: Any, days_ahead: int = 7) -> dict[str, Any]:
    """List upcoming primary-calendar events in Asia/Jerusalem."""
    if not 1 <= days_ahead <= 365:
        raise ValueError("days_ahead must be between 1 and 365.")

    now = datetime.now(JERUSALEM_TZ)
    end = now + timedelta(days=days_ahead)
    response = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            timeZone=TIMEZONE_NAME,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = [format_event(ev) for ev in response.get("items", [])]
    return {
        "timezone": TIMEZONE_NAME,
        "from": now.isoformat(),
        "to": end.isoformat(),
        "count": len(events),
        "events": events,
    }


def find_free_slots(service: Any, date: str, duration_minutes: int = 30) -> dict[str, Any]:
    """Find free intervals of at least duration_minutes on date (08:00-20:00 Asia/Jerusalem)."""
    if duration_minutes < 1:
        raise ValueError("duration_minutes must be at least 1.")

    target_date = date_cls.fromisoformat(date.strip())
    window_start = datetime.combine(target_date, time(WORK_START_HOUR, 0), tzinfo=JERUSALEM_TZ)
    window_end = datetime.combine(target_date, time(WORK_END_HOUR, 0), tzinfo=JERUSALEM_TZ)

    response = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=window_start.isoformat(),
            timeMax=window_end.isoformat(),
            timeZone=TIMEZONE_NAME,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    slots = compute_free_slots(
        response.get("items", []), window_start, window_end, duration_minutes
    )
    return {
        "date": target_date.isoformat(),
        "timezone": TIMEZONE_NAME,
        "window": f"{WORK_START_HOUR:02d}:00-{WORK_END_HOUR:02d}:00",
        "duration_minutes": duration_minutes,
        "free_slots": slots,
    }


def create_event(
    service: Any, title: str, start: str, end: str, description: str = ""
) -> dict[str, Any]:
    """Create a Google Calendar event on the primary calendar in Asia/Jerusalem."""
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("title must not be empty.")

    start_dt = parse_dt(start)
    end_dt = parse_dt(end)
    if end_dt <= start_dt:
        raise ValueError("end must be after start.")

    body = {
        "summary": clean_title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE_NAME},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE_NAME},
    }
    created = service.events().insert(calendarId="primary", body=body).execute()
    return {
        "status": "event_created",
        "timezone": TIMEZONE_NAME,
        "event": format_event(created),
    }
