from sqlalchemy import Column, Integer, String, Float, Date, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class CurrencyData(Base):
    __tablename__ = 'currency_data'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    currency_id = Column(Integer, ForeignKey('currency.id'))


class Model(Base):
    __tablename__ = 'model'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    path = Column(String)
    type = Column(String)