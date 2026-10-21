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

Copy `.env.example` to `.env` if `.env` does not exist. Put your Canvas key and a separate randomly generated server token in it:

```dotenv
CANVAS_API_KEY=your_actual_canvas_key
MCP_SERVER_TOKEN=your_random_server_token
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
Every MCP request requires `Authorization: Bearer YOUR_SERVER_TOKEN`.
The server refuses to start if `MCP_SERVER_TOKEN` is missing or shorter than 32 characters.
Generate the token with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Enter the server token in the client's Bearer-token or Authorization-header settings;
keep the Canvas key only on this computer. Clients that require OAuth discovery
instead of a preconfigured token need a different authentication setup.
This is one shared credential with access to all current tools. To revoke it,
replace it in `.env`, restart the server, and update the client.

## Windows tunnel requirement: cloudflared

`cloudflared` is a separate Windows program required for Cloudflare HTTPS tunnels.
It is not installed by pip. The Python packages remain listed in `requirements.txt`.
Install cloudflared on the computer running this server:

```powershell
winget install --id Cloudflare.cloudflared --exact --source winget
```

Alternatively, download the standalone `cloudflared-windows-amd64.exe` from
Cloudflare's official GitHub releases, verify its published SHA-256 checksum, and
save it as `cloudflared.exe` in a folder on your user PATH. On KNOWLEDGE it is
installed in `%USERPROFILE%\.local\bin` (version 2026.10.2).

Open a new terminal after installation, then confirm it is available:

```powershell
cloudflared --version
```

After adding and testing MCP client authentication, run the server and start a
Quick Tunnel in a separate terminal:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Use the generated HTTPS address with `/mcp` appended in the MCP client. The address
changes when a new Quick Tunnel is created, and the tunnel must remain running.
Installing cloudflared alone does not start a tunnel or add authentication.
Official downloads: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/

## Adding more services

Give each service its own variable in `.env`, for example `WEATHER_API_KEY`.
Read it in Python with `os.getenv("WEATHER_API_KEY")` and use it in that service's
API requests. You must also write and register the corresponding MCP tools;
adding an API key alone does not add an integration.

`python-dotenv` loads the file; `fastmcp` provides the MCP server. `tzdata` supplies
timezone data on Windows, but the current script does not use it yet.

## Connection checks on KNOWLEDGE (2026-10-20)

The local MCP endpoint returned its three tools, and a real `get_courses` call
successfully fetched Canvas data. The Cloudflare endpoint rejected missing and
incorrect tokens with HTTP 401 and returned HTTP 200 with the correct token.
However, reading the full authenticated response through the public endpoint
failed on the testing laptop. A successful connection from Lucas has not yet
been confirmed. HTTP 200 alone does not establish that the complete exchange works.

The user reported adding an Avast exception for `http://127.0.0.1:8000/*`;
local HTTP responses were readable afterward. The public HTTPS certificate
was still issued by Avast Web/Mail Shield, showing that Avast was inspecting
that connection. Its role in the remaining read failure has not been confirmed.

The Python server and tunnel must both keep running. They do not automatically
start after reboot, and sleep or a lost connection can interrupt access.
Do not commit `.env`, live access tokens, or temporary tunnel logs to Git.
