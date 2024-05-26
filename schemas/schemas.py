from typing import Optional

from pydantic import BaseModel, constr
from datetime import date


class PredictionRequest(BaseModel):
    model_name: str
    currency: str
    date: date

    class Config:
        from_attributes = True  # Обновлено для Pydantic v2
        protected_namespaces = ()

class User(BaseModel):
    username: str

    class Config:
        from_attributes = True
        protected_namespaces = ()

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None