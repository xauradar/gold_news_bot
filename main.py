from flask import Flask
import threading
import time
from parser import fetch_calendar_data
from logic import process_events

app = Flask(__name__)

def run_bot():
    while True:
        try:
            events = fetch_calendar_data()
            process_events(events)
        except Exception as e:
            print("Error:", e)
        time.sleep(60)  # Check every 60 seconds

@app.route("/")
def home():
    return "Economic Calendar Bot is running!"

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=8080)
