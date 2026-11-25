# gmail-calendar

An MCP server in Python built with the official MCP Python SDK (`MCPServer`, the `mcp` 2.x successor to `FastMCP`) and `stdio` transport, providing safe Gmail and Google Calendar tools in the `Asia/Jerusalem` time zone.

## Safety & Credentials

- Reads Google OAuth files (`client_secret*.json` and `token.json`) from the directory specified by `GOOGLE_PRIVATE_DIR`.
- Never copies credentials into this repository, never prints secrets, and never opens a browser.
- Never sends emails or deletes emails, drafts, or calendar events.

## Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/)
- An existing private directory containing `client_secret*.json` and `token.json`

## Installation

```bash
uv sync
```

## Running the Server

Set `GOOGLE_PRIVATE_DIR` to the folder containing your Google client and token files, then start the server over `stdio`:

```bash
export GOOGLE_PRIVATE_DIR="/Users/pirogan4ik/Desktop/private"
uv run gmail-calendar
```

You can also run it via the module entrypoint:

```bash
GOOGLE_PRIVATE_DIR="/Users/pirogan4ik/Desktop/private" uv run python -m gmail_calendar
```

## MCP Client Configuration

Example `mcpServers` entry for an MCP client (such as Claude Desktop, Cursor, or Antigravity):

```json
{
  "mcpServers": {
    "gmail-calendar": {
      "command": "uv",
      "args": ["--directory", "/Users/pirogan4ik/Desktop/שיעור 7", "run", "gmail-calendar"],
      "env": {
        "GOOGLE_PRIVATE_DIR": "/Users/pirogan4ik/Desktop/private"
      }
    }
  }
}
```

## Exposed Tools

1. `search_emails(query, max_results=10)` — Search Gmail messages using standard Gmail query syntax.
2. `read_email(message_id)` — Read headers and body of a single Gmail message.
3. `create_draft(to, subject, body)` — Create a Gmail draft only (never sends).
4. `list_events(days_ahead=7)` — List upcoming primary-calendar events in `Asia/Jerusalem`.
5. `find_free_slots(date, duration_minutes=30)` — Find open slots on `YYYY-MM-DD` between `08:00` and `20:00` `Asia/Jerusalem`.
6. `create_event(title, start, end, description="")` — Create a primary-calendar event using ISO 8601 times in `Asia/Jerusalem`.
