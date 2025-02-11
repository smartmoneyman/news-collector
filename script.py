import os
import requests
import json
from bs4 import BeautifulSoup
import yfinance as yf
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from googletrans import Translator

# Инициализация Sentiment Analyzer и Переводчика
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()
translator = Translator()

# Получаем Webhook из переменных окружения
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
print(f"✅ Webhook загружен: {bool(DISCORD_WEBHOOK_URL)}")

# 🔹 Настройки
TICKERS = ["PLTR", "AMD", "PYPL"]  # Можно добавить другие акции
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

# 🔹 Фильтрация новостей по тональности и перевод
def analyze_sentiment(news_list):
    results = []
    for news in news_list:
        sentiment_score = sia.polarity_scores(news["title"])["compound"]

        # Присваиваем текстовую оценку тональности
        if sentiment_score > 0.3:
            sentiment_text = "📈 Позитивная"
        elif sentiment_score < -0.3:
            sentiment_text = "📉 Негативная"
        else:
            sentiment_text = "⚖️ Нейтральная"

        # Перевод заголовка на русский
        try:
            translated_title = translator.translate(news["title"], src="en", dest="ru").text
        except Exception as e:
            print(f"⚠️ Ошибка перевода: {e}")
            translated_title = news["title"]  # Оставляем оригинал, если перевод не сработал

        news["sentiment_score"] = sentiment_score
        news["sentiment_text"] = sentiment_text
        news["translated_title"] = translated_title
        results.append(news)

    return results

# 🔹 Функция отправки в Discord
def send_to_discord(news, ticker):
    if DISCORD_WEBHOOK_URL:
        message = (
            f"📢 **[{ticker}] Новость**\n"
            f"**{news['translated_title']}**\n"
            f"🔗 {news['link']}\n"
            f"📊 Тональность: {news['sentiment_text']} ({news['sentiment_score']:.2f})"
        )
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
        if abs(news_item["sentiment_score"]) >= SENTIMENT_THRESHOLD:
            unique_id = f"{ticker}-{news_item['title']}"
            if unique_id not in sent_news:
                send_to_discord(news_item, ticker)
                sent_news.add(unique_id)  # Запоминаем отправленную новость
