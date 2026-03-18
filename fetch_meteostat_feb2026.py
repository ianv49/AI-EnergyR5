import requests
import json
from datetime import datetime
import logging

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.FileHandler('logs/meteostat_fetch.log'), logging.StreamHandler()])
logger = logging.getLogger("meteostat_fetch")

# Manila
LAT, LON = 14.5995, 120.9842

# RapidAPI Meteostat
RAPIDAPI_KEY = "8e71ca59demsh1b87e385d8d80c4p1fb17djsnedd585a128aa"
HOST = "meteostat.p.rapidapi.com"

def fetch_meteostat_feb2026():
    """Fetch Feb 2026 Manila hourly/daily; save data/meteostat_feb2026.txt. Real web sensor data."""

    url_hourly = "https://meteostat.p.rapidapi.com/point/hourly"
    url_daily = "https://meteostat.p.rapidapi.com/point/daily"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": HOST
    }
    
    params = {"lat": LAT, "lon": LON, "start": "2026-02-01", "end": "2026-02-28"}  # Feb 2026 scope
    
    data_list = []
    
    # Hourly (primary for DB ingest)
    try:
        logger.info("Fetching hourly Feb 2026...")
        r = requests.get(url_hourly, headers=headers, params=params, timeout=60, verify=False)
        r.raise_for_status()
        hourly = r.json()
        data_list.append({"type": "hourly", "params": params, "raw": hourly, "fields": ["time", "temp", "rhum", "wspd", "coco", "rsds"]})
        logger.info(f"Hourly: {len(hourly.get('data', []))} records (~{28*24}=672 expected)")
    except Exception as e:
        logger.error(f"Hourly fail: {e}")
    
    # Daily (summary)
    try:
        logger.info("Fetching daily...")
        r = requests.get(url_daily, headers=headers, params=params, timeout=60, verify=False)
        r.raise_for_status()
        daily = r.json()
        data_list.append({"type": "daily", "params": params, "raw": daily, "fields": ["tavg", "tmin", "tmax", "wspd"]})
        logger.info(f"Daily: {len(daily.get('data', []))} records (28 expected)")
    except Exception as e:
        logger.error(f"Daily fail: {e}")
    
    # Save raw JSON
    txt = f"# Meteostat Feb 2026 Real Web Data ({datetime.now()})\nLat/Lon: {LAT}/{LON}\nScope: 2026-02-01 to 2026-02-28\n\n"
    for entry in data_list:
        txt += f"\n=== {entry['type'].upper()} ({len(entry['raw'].get('data', []))} records) ===\n"
        txt += json.dumps(entry['raw'], indent=2) + "\n"
    
    with open("data/meteostat_feb2026.txt", "w") as f:
        f.write(txt)
    logger.info("✅ Saved data/meteostat_feb2026.txt")
    
    print(f"✅ Fetch complete: {len(data_list)} datasets saved.")
    print("Next: py ingest_meteostat_feb2026.py")
    return data_list

if __name__ == "__main__":
    result = fetch_meteostat_feb2026()
    print("Check logs/meteostat_fetch.log & data/meteostat_feb2026.txt (~672 hourly rows)")

