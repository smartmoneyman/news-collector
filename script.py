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
def get_yahoo_news(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    news_list = []
    
    for article in soup.find_all("li", class_="js-stream-content"):
        title_tag = article.find("h3")
        link_tag = article.find("a")
        if title_tag and link_tag:
            title = title_tag.text
            link = "https://finance.yahoo.com" + link_tag["href"]
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
