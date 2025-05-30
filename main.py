from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import datetime
import pytz

TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
CHAT_ID = '7042701868'

KEYWORDS = [ "CPI", "PPI", "NFP", "FOMC", "Federal Funds", "Unemployment",
    "Retail Sales", "ISM", "GDP", "Inflation", "Jobless Claims",
    "Consumer Confidence", "Trade Balance", "Industrial Production",
    "Housing Starts", "Durable Goods", "Fed Speak", "Interest Rate",
    "Labor Market", "Wage Growth"]

bot = Bot(token=TOKEN)
app = Flask(__name__)
sent_alerts = set()

@app.route('/')
def home():
    return 'Gold News Bot is running!'

def get_news_from_forexfactory():
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

            color = "🟡 Low"
            if "High" in impact_title:
                color = "🔴 High"
            elif "Medium" in impact_title:
                color = "🟠 Medium"

            title = row.find("td", class_="calendar__event").text.strip()
            time_str = row.find("td", class_="calendar__time").text.strip()

            if ":" in time_str and any(k in title for k in KEYWORDS):
                news_list.append({
                    "time": time_str,
                    "title": title,
                    "impact": color,
                    "actual": "-",
                    "forecast": "-",
                    "previous": "-",
                    "source": "ForexFactory"
                })
        except:
            continue

    return news_list

def get_news_from_cryptocraft():
    url = "https://www.cryptocraft.com/calendar"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    events = soup.select("tr.js-event-item")

    news_list = []
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

            if ":" in time_str and any(k in title for k in KEYWORDS):
                color = "🟡 Low"
                if "High" in impact:
                    color = "🔴 High"
                elif "Medium" in impact:
                    color = "🟠 Medium"

                news_list.append({
                    "time": time_str,
                    "title": title,
                    "impact": color,
                    "actual": actual_val,
                    "forecast": forecast_val,
                    "previous": previous_val,
                    "source": "CryptoCraft"
                })
        except:
            continue

    return news_list

def notify():
    while True:
        now_utc = datetime.datetime.utcnow()
        tehran_tz = pytz.timezone('Asia/Tehran')
        utc_tz = pytz.timezone('UTC')
        news_items = get_news_from_forexfactory() + get_news_from_cryptocraft()

        for item in news_items:
            try:
                time_str = item["time"]
                title = item["title"]
                color = item["impact"]
                actual = item["actual"]
                forecast = item["forecast"]
                previous = item["previous"]
                source = item["source"]

                h, m = map(int, time_str.split(':'))
                event_time_utc = now_utc.replace(hour=h, minute=m, second=0, microsecond=0)
                if event_time_utc < now_utc:
                    event_time_utc += datetime.timedelta(days=1)

                diff = (event_time_utc - now_utc).total_seconds()

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
                    if abs(diff - seconds) < 150:
                        alert_key = f"{event_time_utc}_{title}_{seconds}"
                        if alert_key not in sent_alerts:
                            sent_alerts.add(alert_key)
                            tehran_time = event_time_utc.replace(tzinfo=utc_tz).astimezone(tehran_tz)
                            tehran_time_str = tehran_time.strftime("%H:%M")

                            bot.send_message(
                                chat_id=CHAT_ID,
                                text=(
                                    f"{color} News Alert! ({source})\n"
                                    f"📰 {title}\n"
                                    f"🕑 UTC: {time_str} | Tehran: {tehran_time_str}\n"
                                    f"📊 Actual: {actual}\n"
                                    f"📈 Forecast: {forecast}\n"
                                    f"📉 Previous: {previous}\n"
                                    f"{label} before the event."
                                )
                            )
            except:
                continue

        time.sleep(300)

threading.Thread(target=notify, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
if __name__ == '__main__':
    send_telegram_message("🔥 تست اتصال به ربات تلگرام موفق بود.")
    app.run(host='0.0.0.0', port=8080)
