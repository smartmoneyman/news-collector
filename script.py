import os
import requests
import json
from bs4 import BeautifulSoup
import yfinance as yf
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Инициализация Sentiment Analyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Получаем Webhook из переменных окружения
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
print(f"✅ Webhook загружен: {bool(DISCORD_WEBHOOK_URL)}")

# 🔹 Настройки
TICKERS = ["AAPL", "TSLA", "MSFT"]  # Можно добавить другие акции
SENTIMENT_THRESHOLD = 0.3  # Минимальный порог тональности для отправки (0.3 - средний, 0.5 - сильный)

# 🔹 Функция получения новостей с Yahoo Finance API
def get_yahoo_news(ticker):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Ошибка запроса: {response.status_code} для {ticker}")
        return []

    data = response.json()
    news_list = []

    if "news" in data:
        for article in data["news"]:
            title = article.get("title", "Без заголовка")
            link = article.get("link", "")
            if title and link:
                news_list.append({"title": title, "link": link})

    print(f"🔍 Найдено {len(news_list)} новостей для {ticker}")
    return news_list

# 🔹 Фильтрация новостей по тональности
def analyze_sentiment(news_list):
    results = []
    for news in news_list:
        sentiment = sia.polarity_scores(news["title"])
        news["sentiment"] = sentiment["compound"]
        results.append(news)

    return results

# 🔹 Функция отправки в Discord
def send_to_discord(news, ticker):
    if DISCORD_WEBHOOK_URL:
        message = f"📢 **[{ticker}] Новость**\n**{news['title']}**\n🔗 {news['link']}\n📊 Тональность: {news['sentiment']:.2f}"
        payload = {"content": message}

        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(f"✅ Уведомление отправлено в Discord для {ticker}!")
        else:
            print(f"⚠️ Ошибка отправки: {response.status_code} для {ticker}")
    else:
        print("⚠️ DISCORD_WEBHOOK_URL не установлен!")

# 🔹 Лог отправленных новостей, чтобы избежать дублирования
sent_news = set()

# 🔹 Основной процесс
for ticker in TICKERS:
    news = get_yahoo_news(ticker)

    if not news:
        print(f"⚠️ Новости не найдены для {ticker}, пропускаем.")
        continue

    analyzed_news = analyze_sentiment(news)

    for news_item in analyzed_news:
        if abs(news_item["sentiment"]) >= SENTIMENT_THRESHOLD:
            unique_id = f"{ticker}-{news_item['title']}"
            if unique_id not in sent_news:
                send_to_discord(news_item, ticker)
                sent_news.add(unique_id)  # Запоминаем отправленную новость
