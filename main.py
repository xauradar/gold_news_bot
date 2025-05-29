from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import datetime

# Your bot token and chat ID
TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
CHAT_ID = '7042701868'

# News keywords (gold-related)
KEYWORDS = [ "CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment",
    "Retail Sales", "ISM", "GDP", "Inflation", "Jobless Claims",
    "Consumer Confidence", "Trade Balance", "Industrial Production",
    "Housing Starts", "Durable Goods", "Fed Speak", "Interest Rate",
    "Labor Market", "Wage Growth"]
# Initialize bot
bot = Bot(token=TOKEN)

# Initialize Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Gold News Bot is running!'

# To avoid duplicate alerts
sent_alerts = set()

# Function to fetch news
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

            color = ""
            if "High" in impact_title:
                color = "🔴 High"
            elif "Medium" in impact_title:
                color = "🟠 Medium"
            elif "Low" in impact_title:
                color = "🟡 Low"

            title = row.find("td", class_="calendar__event").text.strip()
            time_str = row.find("td", class_="calendar__time").text.strip()

            if ":" in time_str and any(k in title for k in KEYWORDS):
                news_list.append((time_str, title, color))
        except:
            continue

    return news_list

# Notify logic
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

                alert_windows = {
                    7200: "⏰ 2 hours",
                    6600: "⏰ 1 hour 50 minutes",
                    6900: "⏰ 1 hour 55 minutes",
                    7500: "⏰ 2 hours 5 minutes",
                    7800: "⏰ 2 hours 10 minutes",
                    3600: "⏰ 1 hour",
                    3300: "⏰ 55 minutes",
                    3900: "⏰ 1 hour 5 minutes",
                    4200: "⏰ 1 hour 10 minutes"
                }

                for seconds, label in alert_windows.items():
                    if abs(diff - seconds) < 150:  # ±2.5 minutes margin
                        alert_key = f"{event_time}_{title}_{seconds}"
                        if alert_key not in sent_alerts:
                            sent_alerts.add(alert_key)
                            bot.send_message(
                                chat_id=CHAT_ID,
                                text=f"{color} News Alert!\n📰 {title}\n🕑 Scheduled: {time_str} UTC\n{label} before the event."
                            )
            except:
                continue

        time.sleep(300)

# Start background thread
threading.Thread(target=notify, daemon=True).start()

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
