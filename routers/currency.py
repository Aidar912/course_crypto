from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from utils import crud
from db import models
from schemas import schemas
from db.database import get_db
from utils.utils import process_csv

router = APIRouter(
    prefix="/currencies",
    tags=["currencies"],
)

@router.post("/", response_model=schemas.Currency)
def create_currency(currency: schemas.CurrencyCreate, db: Session = Depends(get_db)):
    db_currency = crud.get_currency_by_name(db, name=currency.name)
    if db_currency:
        raise HTTPException(status_code=400, detail="Currency already registered")
    return crud.create_currency(db=db, currency=currency)

@router.get("/{currency_id}", response_model=schemas.Currency)
def read_currency(currency_id: int, db: Session = Depends(get_db)):
    db_currency = crud.get_currency(db, currency_id=currency_id)
    if db_currency is None:
        raise HTTPException(status_code=404, detail="Currency not found")
    return db_currency

@router.post("/{currency_id}/data", response_model=List[schemas.CurrencyData])
def upload_currency_data(currency_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_currency = crud.get_currency(db, currency_id=currency_id)
    if db_currency is None:
        raise HTTPException(status_code=404, detail="Currency not found")
    currency_data_list = process_csv(file.file)
    for data in currency_data_list:
        crud.create_currency_data(db=db, currency_data=schemas.CurrencyDataCreate(**data), currency_id=currency_id)
    return crud.get_currency_data(db, currency_id=currency_id)
