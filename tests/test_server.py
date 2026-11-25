"""Unit and stdio protocol tests for gmail-calendar."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from unittest.mock import MagicMock
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from gmail_calendar import auth, calendar_tools, gmail_tools, mcp


class TestServerRegistration(unittest.TestCase):
    def test_exact_tools_exposed(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        names = [t.name for t in tools]
        self.assertEqual(
            names,
            [
                "search_emails",
                "read_email",
                "create_draft",
                "list_events",
                "find_free_slots",
                "create_event",
            ],
        )
        for t in tools:
            self.assertTrue(t.description and len(t.description.strip()) > 10)


class TestAuthValidation(unittest.TestCase):
    def test_requires_env_var(self) -> None:
        old = auth._cached_creds
        auth._cached_creds = None
        try:
            with unittest.mock.patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(RuntimeError):
                    auth.load_credentials()
        finally:
            auth._cached_creds = old


class TestGmailTools(unittest.TestCase):
    def test_search_read_and_draft_only(self) -> None:
        service = MagicMock()
        raw_text = base64.urlsafe_b64encode(b"Hello world").decode("ascii")
        users = service.users.return_value
        users.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "m1"}]
        }
        users.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "threadId": "t1",
            "snippet": "Hello",
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "Subject", "value": "Test"}],
                "body": {"data": raw_text},
            },
        }
        users.drafts.return_value.create.return_value.execute.return_value = {
            "id": "d1",
            "message": {"id": "m2"},
        }

        res = gmail_tools.search_emails(service, "from:a@b.com", 5)
        self.assertEqual(res["count"], 1)
        self.assertEqual(gmail_tools.read_email(service, "m1")["body"], "Hello world")
        draft = gmail_tools.create_draft(service, "x@y.com", "Hi", "Body")
        self.assertEqual(draft["status"], "draft_created")
        users.messages.return_value.send.assert_not_called()
        users.drafts.return_value.send.assert_not_called()


class TestCalendarTools(unittest.TestCase):
    def test_find_free_slots_jerusalem(self) -> None:
        service = MagicMock()
        service.events.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "status": "confirmed",
                    "start": {"dateTime": "2026-11-26T09:00:00+02:00"},
                    "end": {"dateTime": "2026-11-26T10:30:00+02:00"},
                },
                {
                    "status": "confirmed",
                    "transparency": "transparent",
                    "start": {"dateTime": "2026-11-26T12:00:00+02:00"},
                    "end": {"dateTime": "2026-11-26T13:00:00+02:00"},
                },
            ]
        }
        result = calendar_tools.find_free_slots(service, "2026-11-26", 60)
        self.assertEqual(result["timezone"], "Asia/Jerusalem")
        self.assertEqual(len(result["free_slots"]), 2)
        self.assertEqual(result["free_slots"][0]["duration_minutes"], 60)
        self.assertEqual(result["free_slots"][1]["duration_minutes"], 570)

    def test_create_event_sets_jerusalem_tz(self) -> None:
        service = MagicMock()
        service.events.return_value.insert.return_value.execute.return_value = {
            "id": "e1",
            "summary": "Sync",
            "start": {"dateTime": "2026-11-26T14:00:00+02:00"},
            "end": {"dateTime": "2026-11-26T15:00:00+02:00"},
        }
        res = calendar_tools.create_event(
            service, "Sync", "2026-11-26T14:00:00", "2026-11-26T15:00:00", "Notes"
        )
        self.assertEqual(res["status"], "event_created")
        body = service.events.return_value.insert.call_args.kwargs["body"]
        self.assertEqual(body["start"]["timeZone"], "Asia/Jerusalem")
        self.assertEqual(body["end"]["timeZone"], "Asia/Jerusalem")


class TestStdioTransport(unittest.TestCase):
    def test_stdio_handshake_and_tools(self) -> None:
        async def run_client() -> list[str]:
            params = StdioServerParameters(
                command="uv",
                args=["--directory", str(Path(__file__).resolve().parent.parent), "run", "gmail-calendar"],
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    return [t.name for t in listed.tools]

        names = asyncio.run(run_client())
        self.assertEqual(len(names), 6)


if __name__ == "__main__":
    unittest.main()
