import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_news():
    url = "https://www.cryptocraft.com/calendar"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table.calendar__table tbody tr")

    events = []
    for row in rows:
        try:
            impact_icon = row.select_one(".calendar__impact span")
            if impact_icon is None:
                continue
            impact_class = impact_icon.get("class", [])
            if "impact--low" in impact_class:
                impact = "low"
            elif "impact--medium" in impact_class:
                impact = "medium"
            elif "impact--high" in impact_class:
                impact = "high"
            else:
                continue

            time_str = row.select_one(".calendar__time").text.strip()
            title = row.select_one(".calendar__event").text.strip()
            actual = row.select_one(".calendar__actual").text.strip()
            forecast = row.select_one(".calendar__forecast").text.strip()
            previous = row.select_one(".calendar__previous").text.strip()

            # Example time_str = "7:00am" or "12:30pm"
            time_obj = datetime.strptime(time_str, "%I:%M%p")
            now = datetime.now()
            full_datetime = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)

            # If time already passed today, assume it’s for tomorrow
            if full_datetime < now:
                full_datetime = full_datetime.replace(day=now.day + 1)

            events.append({
                "datetime": full_datetime.isoformat(),
                "title": title,
                "impact": impact,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
            })
        except Exception as e:
            continue

    return events
