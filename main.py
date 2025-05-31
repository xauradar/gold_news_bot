import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import time
import threading
import re

from flask import Flask
app = Flask(__name__)

# === Your Telegram Bot Info ===
TELEGRAM_BOT_TOKEN = '8009592933:AAHQlnciCn0tiFItcFhOgvtAQ4ACnOxZjfw'
TELEGRAM_CHAT_ID = '7042701868'

# === Sent events cache ===
sent_events = set()
posted_results = set()

# === Timezone ===
tehran_tz = pytz.timezone('Asia/Tehran')

# === URL of the economic calendar ===
URL = 'https://www.cryptocraft.com/calendar'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=payload)

def fetch_events():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('tr.calendar__row')
    events = []

    for row in rows:
        try:
            time_td = row.select_one('td.calendar__time')
            if not time_td or 'No events' in time_td.text:
                continue

            time_str = time_td.text.strip()
            match = re.match(r'(\d{1,2}):(\d{2})(am|pm)', time_str.lower())
            if not match:
                continue
            hour = int(match.group(1))
            minute = int(match.group(2))
            meridiem = match.group(3)
            if meridiem == 'pm' and hour != 12:
                hour += 12
            if meridiem == 'am' and hour == 12:
                hour = 0
            now_tehran = datetime.datetime.now(tehran_tz)
            event_time = now_tehran.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if event_time < now_tehran:
                event_time += datetime.timedelta(days=1)

            impact_td = row.select_one('td.calendar__impact span')
            impact_color = impact_td.get('class', [''])[0] if impact_td else ''
            impact = 'Low'
            if 'impact--low' in impact_color:
                impact = 'Yellow'
            elif 'impact--medium' in impact_color:
                impact = 'Orange'
            elif 'impact--high' in impact_color:
                impact = 'Red'

            title_td = row.select_one('td.calendar__event')
            title = title_td.text.strip() if title_td else 'No title'

            forecast_td = row.select_one('td.calendar__forecast')
            previous_td = row.select_one('td.calendar__previous')
            actual_td = row.select_one('td.calendar__actual')

            forecast = forecast_td.text.strip() if forecast_td else '-'
            previous = previous_td.text.strip() if previous_td else '-'
            actual = actual_td.text.strip() if actual_td else '-'

            events.append({
                'title': title,
                'time': event_time,
                'impact': impact,
                'forecast': forecast,
                'previous': previous,
                'actual': actual
            })
        except Exception as e:
            continue
    return events

def monitor():
    while True:
        try:
            now = datetime.datetime.now(tehran_tz)
            events = fetch_events()
            for event in events:
                title = event['title']
                event_time = event['time']
                delta = (event_time - now).total_seconds()
                impact = event['impact']

                # Send warning
                if 60 <= delta <= 7800 and title not in sent_events and impact in ['Red', 'Orange', 'Yellow']:
                    msg = f"⚠️ Upcoming News\n🕒 {event_time.strftime('%H:%M')} Tehran Time\n📌 <b>{title}</b>\n🔥 Importance: {impact}"
                    send_telegram_message(msg)
                    sent_events.add(title)

                # Send result after release
                if -300 <= delta <= 0 and title not in posted_results and impact in ['Red', 'Orange', 'Yellow']:
                    msg = f"✅ News Released\n📌 <b>{title}</b>\n🕒 {event_time.strftime('%H:%M')} Tehran Time\n🔺Actual: {event['actual']}\n🔸Forecast: {event['forecast']}\n🔹Previous: {event['previous']}"
                    send_telegram_message(msg)
                    posted_results.add(title)

            time.sleep(60)
        except Exception as e:
            print(f"Error in monitor: {e}")
            time.sleep(60)

@app.route('/')
def index():
    return 'CryptoCraft News Monitor is Running!'

if __name__ == '__main__':
    threading.Thread(target=monitor).start()
    app.run(host='0.0.0.0', port=8080)
