# Expense Tracker API

A RESTful API for tracking personal expenses, built with FastAPI, SQLAlchemy, and JWT authentication.

## Features

- JWT-based user registration and login
- Full CRUD for expenses (title, amount, category, date)
- Filter expenses by category
- Spending summary broken down by category
- SQLite database (swap to PostgreSQL for production)
- Auto-generated OpenAPI docs at `/docs`

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API explorer.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Get JWT token |
| GET | /auth/me | Current user info |
| GET | /expenses/ | List your expenses |
| POST | /expenses/ | Add an expense |
| GET | /expenses/summary | Spending by category |
| GET | /expenses/{id} | Get one expense |
| PATCH | /expenses/{id} | Update an expense |
| DELETE | /expenses/{id} | Delete an expense |

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **FastAPI** — high-performance async web framework
- **SQLAlchemy 2** — ORM with SQLite backend
- **Pydantic v2** — request/response validation
- **python-jose** — JWT token handling
- **passlib / bcrypt** — secure password hashing
- **pytest + httpx** — integration test suite
