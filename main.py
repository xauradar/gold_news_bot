from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
import datetime
from telegram import Bot

# Telegram bot info
TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
CHAT_ID = '7042701868'

KEYWORDS = ["CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment", "Retail Sales", "ISM"]
URL = "https://www.forexfactory.com/calendar.php"

bot = Bot(token=TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def get_news():
    try:
        res = requests.get(URL)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all("tr", class_="calendar__row")
        news_list = []
        for row in rows:
            impact = row.find("td", class_="calendar__impact").find("span")
            if not impact or "High" not in impact.get("title", ""):
                continue
            title = row.find("td", class_="calendar__event").text.strip()
            time_str = row.find("td", class_="calendar__time").text.strip()
            if any(k in title for k in KEYWORDS) and ":" in time_str:
                news_list.append((time_str, title))
        return news_list
    except:
        return []

def notify():
    while True:
        try:
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
        except:
            pass
        time.sleep(300)

def run():
    app.run(host='0.0.0.0', port=8080)

# Run web + bot threads
threading.Thread(target=notify).start()
threading.Thread(target=run).start()
