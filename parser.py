import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.cryptocraft.com/calendar"

def fetch_calendar_data():
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    
    events = []
    rows = soup.select("table.calendar__table tbody tr")

    for row in rows:
        # Skip rows with "spacer" class
        if "spacer" in row.get("class", []):
            continue

        try:
            time_str = row.select_one(".calendar__time").text.strip()
            currency = row.select_one(".calendar__currency").text.strip()
            impact_icon = row.select_one(".calendar__impact i")
            event_title = row.select_one(".calendar__event").text.strip()

            forecast = row.select_one(".calendar__forecast").text.strip()
            previous = row.select_one(".calendar__previous").text.strip()
            actual = row.select_one(".calendar__actual").text.strip()

            # Determine impact level based on icon color class
            impact_level = "low"
            if impact_icon and "impact--high" in impact_icon.get("class", []):
                impact_level = "high"
            elif impact_icon and "impact--medium" in impact_icon.get("class", []):
                impact_level = "medium"

            # Convert time string (e.g., "7:00am") to 24-hour format today
            event_time = datetime.strptime(time_str, "%I:%M%p")
            now = datetime.now()
            event_time = event_time.replace(year=now.year, month=now.month, day=now.day)

            events.append({
                "title": event_title,
                "currency": currency,
                "impact": impact_level,
                "time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "forecast": forecast,
                "previous": previous,
                "actual": actual
            })

        except Exception as e:
            print("Parser error:", e)
            continue

    return events
