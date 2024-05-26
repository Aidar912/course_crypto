import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from textblob import TextBlob
from schemas.schemas import ScrapeRequest
from scraper.scraper.twitter_scraper import Twitter_Scraper
import os
import asyncio
from db.database import engine
from db.models import Base
from routers import auth, users, predict, model, currency

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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Twitter Scraper</title>
        </head>
        <body>
            <h1>Twitter Scraper</h1>
            <form action="" onsubmit="sendMessage(event)">
                <input type="text" id="keyword" placeholder="Enter keyword" required>
                <select id="query_type">
                    <option value="hashtag">Hashtag</option>
                    <option value="username">Username</option>
                    <option value="query">Query</option>
                </select>
                <button type="submit">Start Scraping</button>
            </form>
            <ul id="tweets"></ul>
            <script>
                const ws = new WebSocket("ws://localhost:8000/ws");

                ws.onmessage = function(event) {
                    const tweets = document.getElementById("tweets");
                    const tweet = document.createElement("li");
                    tweet.innerText = event.data;
                    tweets.appendChild(tweet);
                };

                function sendMessage(event) {
                    event.preventDefault();
                    const keyword = document.getElementById("keyword").value;
                    const query_type = document.getElementById("query_type").value;
                    ws.send(JSON.stringify({ keyword, query_type }));
                }
            </script>
        </body>
    </html>
    """

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

app.include_router(model.router, prefix="/api/models", tags=["Models"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(currency.router, prefix="/api/currency", tags=["currency"])





