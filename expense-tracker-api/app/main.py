from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, expenses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0", description="Track personal expenses with a clean REST API")

app.include_router(users.router, prefix="/auth", tags=["auth"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])


@app.get("/")
def root():
    return {"message": "Expense Tracker API", "docs": "/docs"}
