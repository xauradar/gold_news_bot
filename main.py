from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import datetime

TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
CHAT_ID = '7042701868'

KEYWORDS = [
    "CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment",
    "Retail Sales", "ISM", "GDP", "Inflation", "Jobless Claims",
    "Consumer Confidence", "Trade Balance", "Industrial Production",
    "Housing Starts", "Durable Goods", "Fed Speak", "Interest Rate",
    "Labor Market", "Wage Growth"
]

bot = Bot(token=TOKEN)
app = Flask(__name__)

notified_initial = set()
notified_final = set()

@app.route('/')
def home():
    return 'CryptoCraft Economic News Bot is active!'

def fetch_news():
    url = "https://www.cryptocraft.com/calendar"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    events = soup.select("tr.js-event-item")

    news_items = []
    for event in events:
        try:
            title = event.select_one(".calendar__event-title").get_text(strip=True)
            impact = event.select_one(".calendar__impact-icon span")["title"]
            time_str = event.select_one(".calendar__time").get_text(strip=True)

            actual = event.select_one(".calendar__actual")
            forecast = event.select_one(".calendar__forecast")
            previous = event.select_one(".calendar__previous")

            actual_val = actual.get_text(strip=True) if actual else "-"
            forecast_val = forecast.get_text(strip=True) if forecast else "-"
            previous_val = previous.get_text(strip=True) if previous else "-"

            if ":" not in time_str:
                continue

            impact_icon = "🟡 Low"
            if "High" in impact:
                impact_icon = "🔴 High"
            elif "Medium" in impact:
                impact_icon = "🟠 Medium"

            if any(k.lower() in title.lower() for k in KEYWORDS):
                news_items.append({
                    "time": time_str,
                    "title": title,
                    "impact": impact_icon,
                    "actual": actual_val,
                    "forecast": forecast_val,
                    "previous": previous_val,
                })
        except Exception as e:
            continue

    return news_items

def notifier():
    while True:
        now = datetime.datetime.now()
        news_list = fetch_news()

        for news in news_list:
            try:
                title = news["title"]
                impact = news["impact"]
                time_str = news["time"]
                actual = news["actual"]
                forecast = news["forecast"]
                previous = news["previous"]

                h, m = map(int, time_str.split(":"))
                event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if event_time < now:
                    event_time += datetime.timedelta(days=1)

                seconds_until = (event_time - now).total_seconds()
                key = f"{event_time}_{title}"

                # Send initial alert (between 1 min and 2h10m before release)
                if 60 <= seconds_until <= 7800 and key not in notified_initial:
                    notified_initial.add(key)
                    bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"{impact} Upcoming Economic Event\n"
                            f"📰 Title: {title}\n"
                            f"🕒 Time: {time_str} (Tehran Time)\n"
                            f"📈 Forecast: {forecast}\n"
                            f"📉 Previous: {previous}\n"
                            f"⏳ {int(seconds_until / 60)} minutes left until release."
                        )
                    )

                # Send final alert once actual value is published
                if actual not in ("-", "") and key not in notified_final:
                    notified_final.add(key)
                    bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"{impact} 🔔 Released\n"
                            f"📰 Title: {title}\n"
                            f"🕒 Time: {time_str} (Tehran Time)\n"
                            f"✅ Actual: {actual}\n"
                            f"📈 Forecast: {forecast}\n"
                            f"📉 Previous: {previous}"
                        )
                    )

            except Exception as e:
                continue

        time.sleep(60)

threading.Thread(target=notifier, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
