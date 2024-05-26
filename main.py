import asyncio
import json
import os
from typing import Optional

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from textblob import TextBlob

from db.database import engine
from db.models import Base
from routers import auth, users, predict, model, currency
from schemas.schemas import ScrapeRequest, DataResponse, PriceRequest
from scraper.scraper.twitter_scraper import Twitter_Scraper

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = FastAPI(
    title="Currency Prediction API",
    description="API для предсказания курса валют с использованием моделей машинного обучения",
    version="1.0.0",
    docs_url="/docs",  # URL для документации Swagger
    redoc_url="/redoc"  # URL для документации ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

CSV_FILES = {
    "bitcoin": "tweets_data/btc_done.csv",
    "ethereum": "tweets_data/eth_done.csv",
    "near": "tweets_data/near_done.csv",
}


def get_crypto_price(date: str, currency: str) -> float:
    # Преобразуем дату в формат dd-mm-yyyy
    date_parts = date.split("-")
    formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"

    API_URL = f"https://api.coingecko.com/api/v3/coins/{currency}/history?date={formatted_date}"

    response = requests.get(API_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                            detail=f"Ошибка при запросе к API: {response.status_code}")

    data = response.json()
    try:
        price = data['market_data']['current_price']['usd']
        return price
    except KeyError:
        raise HTTPException(status_code=404, detail="Цена на указанную дату не найдена")


@app.post("/get_price/")
async def get_price(request: PriceRequest):
    price = get_crypto_price(request.date, request.currency)
    return {"date": request.date, "currency": request.currency, "price": price}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            scrape_request = ScrapeRequest.parse_raw(data)
            await scrape_tweets_continuously(scrape_request, websocket)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")

async def scrape_tweets_continuously(request: ScrapeRequest, websocket: WebSocket):
    print(f"Starting to scrape tweets for keyword: {request.keyword}, query type: {request.query_type}")
    scraper = Twitter_Scraper(
        mail=os.getenv("TWITTER_MAIL"),
        username=os.getenv("TWITTER_USERNAME"),
        password=os.getenv("TWITTER_PASSWORD"),
        scrape_username=request.keyword if request.query_type == "username" else None,
        scrape_hashtag=request.keyword if request.query_type == "hashtag" else None,
        scrape_query=request.keyword if request.query_type == "query" else None,
        max_tweets=3,  # По умолчанию брать последние 10 твитов
        scrape_latest=True,  # Обеспечить получение последних твитов
    )
    print("Logging in...")
    scraper.login()
    print("Logged in successfully")

    while True:
        print("Scraping tweets...")
        scraper.scrape_tweets(
            max_tweets=3,  # Здесь явно указано количество твитов
            scrape_username=request.keyword if request.query_type == "username" else None,
            scrape_hashtag=request.keyword if request.query_type == "hashtag" else None,
            scrape_query=request.keyword if request.query_type == "query" else None,
            scrape_latest=True
        )
        data = scraper.get_tweets()
        print(f"Retrieved {len(data)} tweets")
        if not data:
            print("No tweets found")
            break
        for tweet in data:
            try:
                content = tweet[4]
                analysis = TextBlob(content)
                sentiment = analysis.sentiment
                tweet_message = {
                    "author": tweet[0],
                    "time": tweet[2],
                    "content": content,
                    "sentiment": sentiment.polarity,
                    "subjectivity": sentiment.subjectivity,
                }
                await websocket.send_text(json.dumps(tweet_message))  # Отправка деталей твита
                print(f"Sent tweet: {tweet_message}")
            except WebSocketDisconnect:
                print("WebSocket disconnected while sending tweet")
                return
            except Exception as e:
                print(f"Error while sending tweet: {e}")
                return
        await asyncio.sleep(1)  # Небольшая задержка, чтобы избежать быстрого цикла



@app.get("/tweets/{key}", response_model=DataResponse)
async def get_data(key: str, limit: Optional[int] = Query(None, description="Number of rows to return")):
    # Проверяем наличие ключа
    if key not in CSV_FILES:
        raise HTTPException(status_code=404, detail="Key not found")

    # Читаем соответствующий CSV-файл
    try:
        df = pd.read_csv(CSV_FILES[key])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Ограничиваем количество возвращаемых строк
    if limit is not None:
        df = df.head(limit)
    else:
        df = df.head(10)

    # Преобразуем данные в формат для ответа, заменяя NaN на пустые строки и преобразуя все значения в строки
    response_data = {
        "data": df.fillna("").astype(str).values.tolist()
    }

    return response_data

app.include_router(model.router, prefix="/api/models", tags=["Models"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(currency.router, prefix="/api/currency", tags=["currency"])





