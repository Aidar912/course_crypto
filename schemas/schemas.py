from typing import Optional

from pydantic import BaseModel, Field
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

class ModelBase(BaseModel):
    name: str
    type: str = Field(..., pattern="^(pkl|h5)$")

class ModelCreate(ModelBase):
    pass

class ModelUpdate(ModelBase):
    pass

class ModelInDBBase(ModelBase):
    id: int
    path: str
    last_update: date

    class Config:
        orm_mode = True

class Model(ModelInDBBase):
    pass



class CurrencyBase(BaseModel):
    name: str

class CurrencyCreate(CurrencyBase):
    pass

class Currency(CurrencyBase):
    id: int

    class Config:
        orm_mode = True

class CurrencyDataBase(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume_btc: float
    volume_currency: float
    weighted_price: float

class CurrencyDataCreate(CurrencyDataBase):
    pass

class CurrencyData(CurrencyDataBase):
    id: int
    currency_id: int

    class Config:
        orm_mode = True