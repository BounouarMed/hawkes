from fastapi import WebSocket
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Message:
    user: str
    text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%H:%M:%S")
    )

    def to_dict(self) -> dict:
        return {"user": self.user, "text": self.text, "timestamp": self.timestamp}


class ConnectionManager:
    def __init__(self, history_size: int = 50):
        self._rooms: dict[str, list[WebSocket]] = defaultdict(list)
        self._history: dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))

    def room_count(self, room: str) -> int:
        return len(self._rooms[room])

    async def connect(self, websocket: WebSocket, room: str) -> list[dict]:
        await websocket.accept()
        self._rooms[room].append(websocket)
        return [m.to_dict() for m in self._history[room]]

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        try:
            self._rooms[room].remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, room: str, message: Message) -> None:
        self._history[room].append(message)
        payload = {**message.to_dict(), "room": room, "users": self.room_count(room)}
        dead: list[WebSocket] = []
        for ws in list(self._rooms[room]):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)
