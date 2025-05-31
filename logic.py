from datetime import datetime, timedelta
import json
import os
import requests

MEMORY_FILE = "memory.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"alerts": [], "reports": []}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass


def process_events(events):
    memory = load_memory()
    now = datetime.now()

    for event in events:
        try:
            dt = datetime.fromisoformat(event["datetime"])
            delta = (dt - now).total_seconds()

            # 🔴 Step 1: Send alert before event
            if 60 <= delta <= 130 * 60:
                if event["title"] not in memory["alerts"]:
                    msg = f"📢 Upcoming Event ({event['impact'].upper()} Impact)\n🕒 {dt.strftime('%H:%M')} | {event['title']}"
                    send_telegram(msg)
                    memory["alerts"].append(event["title"])

            # 🔵 Step 2: Send result after event
            if -30 * 60 < delta <= 0:
                if event["title"] not in memory["reports"]:
                    msg = (
                        f"📊 Event Released\n"
                        f"🕒 {dt.strftime('%H:%M')} | {event['title']}\n"
                        f"Actual: {event['actual'] or 'N/A'}\n"
                        f"Forecast: {event['forecast'] or 'N/A'}\n"
                        f"Previous: {event['previous'] or 'N/A'}"
                    )
                    send_telegram(msg)
                    memory["reports"].append(event["title"])
        except:
            continue

    # 🔁 Keep memory small
    if len(memory["alerts"]) > 100:
        memory["alerts"] = memory["alerts"][-50:]
    if len(memory["reports"]) > 100:
        memory["reports"] = memory["reports"][-50:]

    save_memory(memory)
