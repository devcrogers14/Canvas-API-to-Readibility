# Canvas Readability MCP server

Exposes three read-only tools: `get_courses()`, `get_assignments(course_id)`,
and `check_modules(course_id)` (course modules and their items).
Assignments are filtered to the current Monday–Sunday week. The script currently
uses the laptop's date for the week and Canvas's UTC date for assignment due dates.

## Setup

Use Python 3.10 or newer. Create a project environment if you do not have one:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` if `.env` does not exist. Put your Canvas key in it:

```dotenv
CANVAS_API_KEY=your_actual_canvas_key
```

The server automatically loads `.env` from the folder containing the Python script,
even if you start it from a different folder. Existing process environment variables
take priority. Save changes and restart the server to load new keys.
The real `.env` is ignored by Git; `.env.example` contains no secrets and can be shared.

## Run

From this project folder:

```powershell
.\.venv\Scripts\python.exe "Canvas API to Readability.py"
```

The HTTP MCP endpoint is `http://127.0.0.1:8000/mcp`.
Responses use JSON instead of SSE. HTTP requests do not retain MCP sessions
(`json_response=True`, `stateless_http=True`).
Press Ctrl+C in its terminal to stop it. This version runs HTTP, not a stdio server.
It has no MCP client authentication yet; keep it local until authentication is added.

## Adding more services

Give each service its own variable in `.env`, for example `WEATHER_API_KEY`.
Read it in Python with `os.getenv("WEATHER_API_KEY")` and use it in that service's
API requests. You must also write and register the corresponding MCP tools;
adding an API key alone does not add an integration.

`python-dotenv` loads the file; `fastmcp` provides the MCP server. `tzdata` supplies
timezone data on Windows, but the current script does not use it yet.
