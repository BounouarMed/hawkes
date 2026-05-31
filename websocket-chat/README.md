# WebSocket Chat

Real-time multi-room chat application built with FastAPI WebSockets. Includes a dark-themed web UI served directly from the API.

## Features

- Multiple chat rooms — join any room by name
- Last 50 messages replayed on join (per room)
- Live user count per room
- System join/leave notifications
- Clean dark web UI, no external dependencies
- All served from a single FastAPI process

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000, enter a room name and your username, click **Join**.

Open multiple browser tabs to simulate multiple users.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Chat web UI |
| `GET /rooms/{room}/count` | Number of connected users |
| `WS /ws/{room}/{username}` | WebSocket connection |

### WebSocket message format

```json
{ "user": "Alice", "text": "Hello!", "timestamp": "14:32:01", "room": "general", "users": 3 }
```

On connect, the server sends a history packet first:
```json
{ "type": "history", "messages": [ ... ] }
```

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **FastAPI** — async web framework + WebSocket support
- **uvicorn** — ASGI server
- **pytest + httpx** — HTTP and WebSocket test client
