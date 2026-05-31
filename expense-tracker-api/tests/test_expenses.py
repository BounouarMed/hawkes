import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _get_token(email="test@example.com", password="secret"):
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def test_register():
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@b.com"


def test_duplicate_register():
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    assert resp.status_code == 400


def test_login():
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    resp = client.post("/auth/login", data={"username": "a@b.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_invalid_login():
    resp = client.post("/auth/login", data={"username": "nobody@x.com", "password": "wrong"})
    assert resp.status_code == 401


def test_create_and_list_expenses():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/expenses/", json={"title": "Lunch", "amount": 12.5, "category": "food"}, headers=headers)
    resp = client.get("/expenses/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Lunch"


def test_filter_by_category():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/expenses/", json={"title": "Lunch", "amount": 10.0, "category": "food"}, headers=headers)
    client.post("/expenses/", json={"title": "Bus", "amount": 3.0, "category": "transport"}, headers=headers)
    resp = client.get("/expenses/?category=food", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["category"] == "food"


def test_summary():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/expenses/", json={"title": "Lunch", "amount": 10.0, "category": "food"}, headers=headers)
    client.post("/expenses/", json={"title": "Bus", "amount": 3.0, "category": "transport"}, headers=headers)
    resp = client.get("/expenses/summary", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 13.0
    assert resp.json()["by_category"]["food"] == 10.0


def test_update_expense():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/expenses/", json={"title": "Coffee", "amount": 2.5, "category": "food"}, headers=headers)
    expense_id = create_resp.json()["id"]
    resp = client.patch(f"/expenses/{expense_id}", json={"amount": 3.0}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 3.0


def test_delete_expense():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/expenses/", json={"title": "Coffee", "amount": 2.5, "category": "food"}, headers=headers)
    expense_id = create_resp.json()["id"]
    del_resp = client.delete(f"/expenses/{expense_id}", headers=headers)
    assert del_resp.status_code == 204
    get_resp = client.get(f"/expenses/{expense_id}", headers=headers)
    assert get_resp.status_code == 404


def test_expenses_isolated_between_users():
    token1 = _get_token("user1@x.com", "pass")
    token2 = _get_token("user2@x.com", "pass")
    client.post("/expenses/", json={"title": "Secret", "amount": 5.0, "category": "misc"}, headers={"Authorization": f"Bearer {token1}"})
    resp = client.get("/expenses/", headers={"Authorization": f"Bearer {token2}"})
    assert resp.json() == []
