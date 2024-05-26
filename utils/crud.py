from sqlalchemy.orm import Session
from schemas import  schemas
from db import models
def get_currency(db: Session, currency_id: int):
    return db.query(models.Currency).filter(models.Currency.id == currency_id).first()

def get_currency_by_name(db: Session, name: str):
    return db.query(models.Currency).filter(models.Currency.name == name).first()

def create_currency(db: Session, currency: schemas.CurrencyCreate):
    db_currency = models.Currency(name=currency.name)
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency

def create_currency_data(db: Session, currency_data: schemas.CurrencyDataCreate, currency_id: int):
    db_currency_data = models.CurrencyData(**currency_data.dict(), currency_id=currency_id)
    db.add(db_currency_data)
    db.commit()
    db.refresh(db_currency_data)
    return db_currency_data

def get_currency_data(db: Session, currency_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.CurrencyData).filter(models.CurrencyData.currency_id == currency_id).offset(skip).limit(limit).all()
