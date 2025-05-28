from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import datetime

# Telegram bot token and chat ID
TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
CHAT_ID = '7042701868'

# News keywords to watch
KEYWORDS = ["CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment", "Retail Sales", "ISM"]

# Telegram Bot setup
bot = Bot(token=TOKEN)

# Flask app setup
app = Flask(__name__)

@app.route('/')
def home():
    return 'Gold News Bot is running!'

# Function to fetch high-impact news from ForexFactory
def get_news():
    url = "https://www.forexfactory.com/calendar.php"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    rows = soup.find_all("tr", class_="calendar__row")
    news_list = []

    for row in rows:
        try:
            impact = row.find("td", class_="calendar__impact").find("span")
            if not impact or "High" not in impact.get("title", ""):
                continue

            title = row.find("td", class_="calendar__event").text.strip()
            time_str = row.find("td", class_="calendar__time").text.strip()

            if any(k in title for k in KEYWORDS) and ":" in time_str:
                news_list.append((time_str, title))
        except:
            continue

    return news_list

# Function to check and send alerts
def notify():
    while True:
        now = datetime.datetime.utcnow()
        news_items = get_news()

        for time_str, title in news_items:
            try:
                h, m = map(int, time_str.split(':'))
                event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if event_time < now:
                    event_time += datetime.timedelta(days=1)

                diff = (event_time - now).total_seconds()
                if 3540 < diff < 3660:
                    bot.send_message(chat_id=CHAT_ID, text=f"⚠️ High Impact News: {title} at {time_str} UTC")
            except:
                continue

        time.sleep(300)  # Check every 5 minutes

# Start notify() in background thread
threading.Thread(target=notify, daemon=True).start()

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
