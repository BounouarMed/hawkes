import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.connection_manager import ConnectionManager, Message

client = TestClient(app)


def test_root_returns_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "WebSocket Chat" in resp.text


def test_room_count_empty():
    resp = client.get("/rooms/emptyroom123/count")
    assert resp.status_code == 200
    assert resp.json()["users"] == 0


def test_message_to_dict():
    msg = Message(user="Alice", text="Hello", timestamp="12:00:00")
    d = msg.to_dict()
    assert d == {"user": "Alice", "text": "Hello", "timestamp": "12:00:00"}


def test_connection_manager_history_limit():
    mgr = ConnectionManager(history_size=3)

    async def run():
        for i in range(5):
            await mgr.broadcast("room", Message("u", f"msg{i}"))
        assert len(mgr._history["room"]) == 3
        assert list(mgr._history["room"])[-1].text == "msg4"

    asyncio.run(run())


def test_websocket_join_receives_history_then_join_msg():
    with client.websocket_connect("/ws/general/Alice") as ws:
        history_pkt = ws.receive_json()
        assert history_pkt["type"] == "history"
        join_msg = ws.receive_json()
        assert "joined" in join_msg["text"]
        assert join_msg["user"] == "System"


def test_websocket_message_broadcast():
    with client.websocket_connect("/ws/room42/Alice") as ws1:
        ws1.receive_json()  # history
        ws1.receive_json()  # join
        with client.websocket_connect("/ws/room42/Bob") as ws2:
            ws2.receive_json()  # history
            ws1.receive_json()  # Bob joined (broadcast to Alice)
            ws2.receive_json()  # Bob joined (echo to Bob)
            ws2.send_text("Hi everyone!")
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()
            assert msg1["text"] == "Hi everyone!"
            assert msg1["user"] == "Bob"
            assert msg2["text"] == "Hi everyone!"
