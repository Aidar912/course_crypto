from datetime import datetime, timedelta
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, HTTPException , status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt , JWTError
from keras.models import load_model
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from db.models import Model
from db.models import User as DBUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "courseWork21"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user



async def load_model(session: Session, model_name: str):
    model_record = session.query(Model).filter(Model.name == model_name).first()
    if model_record is None:
        return None

    if model_record.type == 'pkl':
        return joblib.load(model_record.path)
    elif model_record.type == 'h5':
        return load_model(model_record.path)
    else:
        return None

def prepare_single_input(data, features, target_date):
    if not isinstance(target_date, pd.Timestamp):
        target_date = pd.to_datetime(target_date).date()

    if pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = data['date'].dt.date
    else:
        data['date'] = pd.to_datetime(data['date']).dt.date

    filtered_data = data[data['date'] <= target_date]
    sorted_data = filtered_data.sort_values(by='date', ascending=True)
    if len(sorted_data) < 30:
        raise ValueError("Not enough data to prepare input. Required 30, given {}".format(len(sorted_data)))
    recent_data = sorted_data.tail(30)

    feature_data = recent_data[features]
    X_single = feature_data.to_numpy().reshape(1, 30, len(features))

    return X_single

def safe_convert_to_jsonable(data):
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (np.float32, np.float64)):
        return float(data)
    if isinstance(data, (np.int32, np.int64)):
        return int(data)
    return data


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )