from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.connection_manager import ConnectionManager, Message

app = FastAPI(title="WebSocket Chat")
manager = ConnectionManager()

HTML = (Path(__file__).parent / "static" / "index.html").read_text()


@app.get("/")
async def root() -> HTMLResponse:
    return HTMLResponse(HTML)


@app.get("/rooms/{room}/count")
async def room_count(room: str) -> dict:
    return {"room": room, "users": manager.room_count(room)}


@app.websocket("/ws/{room}/{username}")
async def websocket_endpoint(websocket: WebSocket, room: str, username: str) -> None:
    history = await manager.connect(websocket, room)
    await websocket.send_json({"type": "history", "messages": history})
    await manager.broadcast(room, Message(user="System", text=f"{username} joined the room"))
    try:
        while True:
            text = await websocket.receive_text()
            if text.strip():
                await manager.broadcast(room, Message(user=username, text=text.strip()))
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast(room, Message(user="System", text=f"{username} left the room"))
