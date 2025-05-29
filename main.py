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

# Keywords to watch
KEYWORDS = ["CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment", "Retail Sales", "ISM"]

# Setup bot
bot = Bot(token=TOKEN)

# Setup Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return 'Gold News Bot is running!'

# Function to get news
def get_news():
    url = "https://www.forexfactory.com/calendar.php"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    rows = soup.find_all("tr", class_="calendar__row")
    news_list = []

    for row in rows:
        try:
            impact_span = row.find("td", class_="calendar__impact").find("span")
            if not impact_span:
                continue

            impact_title = impact_span.get("title", "")
            if not any(level in impact_title for level in ["Low", "Medium", "High"]):
                continue

            title = row.find("td", class_="calendar__event").text.strip()
            time_str = row.find("td", class_="calendar__time").text.strip()

            if any(k in title for k in KEYWORDS) and ":" in time_str:
                color = ""
                if "High" in impact_title:
                    color = "🔴"
                elif "Medium" in impact_title:
                    color = "🟠"
                elif "Low" in impact_title:
                    color = "🟡"

                news_list.append((time_str, title, color))
        except:
            continue

    return news_list

# Function to notify
def notify():
    while True:
        now = datetime.datetime.utcnow()
        news_items = get_news()

        for time_str, title, color in news_items:
            try:
                h, m = map(int, time_str.split(':'))
                event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if event_time < now:
                    event_time += datetime.timedelta(days=1)

                diff = (event_time - now).total_seconds()
                if 3540 < diff < 3660:
                    bot.send_message(chat_id=CHAT_ID, text=f"{color} News: {title} at {time_str} UTC")
            except:
                continue

        time.sleep(300)

# Background thread
threading.Thread(target=notify, daemon=True).start()

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
