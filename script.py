import os
import requests
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

# Функция получения новостей
import json

def get_yahoo_news(ticker):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Ошибка запроса: {response.status_code}")
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


# Функция анализа тональности
def analyze_sentiment(news_list):
    results = []
    for news in news_list:
        sentiment = sia.polarity_scores(news["title"])
        news["sentiment"] = sentiment["compound"]
        results.append(news)
    
    return results

# Отправка уведомления в Discord
def send_to_discord(news):
    if DISCORD_WEBHOOK_URL:
        message = f"**{news['title']}**\n🔗 {news['link']}\n📊 Тональность: {news['sentiment']}"
        payload = {"content": message}
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("✅ Уведомление отправлено в Discord!")
        else:
            print(f"⚠️ Ошибка отправки: {response.status_code}")
    else:
        print("⚠️ DISCORD_WEBHOOK_URL не установлен!")

# Основной процесс
ticker = "AAPL"
news = get_yahoo_news(ticker)

if not news:
    print("⚠️ Новости не найдены, бот завершает работу.")
else:
    analyzed_news = analyze_sentiment(news)
    for news in analyzed_news:
        if abs(news["sentiment"]) > 0.0:  # Разрешаем отправлять любые новости
            send_to_discord(news)
