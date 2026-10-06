# Canvas Readability MCP server

This version exposes two read-only tools: `get_courses()` and `get_assignments(course_id)`.
Assignments are filtered to the current Monday–Sunday week in America/Chicago.
Set `CANVAS_TIMEZONE` to another IANA timezone name if needed.

## Setup

Use Python 3.10 or newer and install dependencies with that same interpreter:

```powershell
python -m pip install -r requirements.txt
```

Configure Lucas's MCP client to launch Python with the absolute path to
`Canvas API to Readability.py` as its argument. Supply `CANVAS_API_KEY` in the
server process environment. Use the Python executable where you installed
these dependencies. Do not add `--cli` to the MCP launch arguments.

Example for clients that accept an `mcpServers` configuration (adapt to Lucas's format):

```json
{
  "mcpServers": {
    "canvas": {
      "command": "C:/path/to/python.exe",
      "args": ["C:/path/to/Canvas API to Readability.py"],
      "env": {
        "CANVAS_API_KEY": "YOUR_CANVAS_TOKEN",
        "CANVAS_TIMEZONE": "America/Chicago"
      }
    }
  }
}
```

The server uses local stdio transport. A client that only accepts a remote HTTP
MCP URL needs a different deployment and authentication setup.

## Original interactive menu

```powershell
python "Canvas API to Readability.py" --cli
```

The menu is separate because MCP uses standard input/output for protocol messages.
Grades are percentages when Canvas supplies them; unavailable grades remain null.
