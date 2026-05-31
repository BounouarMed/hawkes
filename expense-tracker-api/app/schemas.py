from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    description: Optional[str] = None
    date: Optional[datetime] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None


class ExpenseOut(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    description: Optional[str]
    date: datetime
    owner_id: int

    model_config = {"from_attributes": True}
