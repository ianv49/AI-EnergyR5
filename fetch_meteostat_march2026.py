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

def fetch_meteostat_march2026():
    """Fetch March 2026 Manila hourly; save data/meteostat_march2026.txt. Real web."""
    url_hourly = "https://meteostat.p.rapidapi.com/point/hourly"
    url_daily = "https://meteostat.p.rapidapi.com/point/daily"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": HOST
    }
    
    params = {"lat": LAT, "lon": LON, "start": "2026-03-01", "end": "2026-03-31"}
    
    data_list = []
    
    # Hourly
    try:
        logger.info("Fetching hourly...")
        r = requests.get(url_hourly, headers=headers, params=params, timeout=60, verify=False)
        r.raise_for_status()
        hourly = r.json()
        data_list.append({"type": "hourly", "params": params, "raw": hourly, "solar_wind": ["rsds", "wspd", "tsun", "wpgt"]})
        logger.info(f"Hourly: {len(hourly.get('data', []))} records")
    except Exception as e:
        logger.error(f"Hourly fail: {e}")
    
    # Daily
    try:
        logger.info("Fetching daily...")
        r = requests.get(url_daily, headers=headers, params=params, timeout=60, verify=False)
        r.raise_for_status()
        daily = r.json()
        data_list.append({"type": "daily", "params": params, "raw": daily, "solar_wind": ["rsds", "wspd", "tsun"]})
        logger.info(f"Daily: {len(daily.get('data', []))} records")
    except Exception as e:
        logger.error(f"Daily fail: {e}")
    
    # Save
    txt = f"# Meteostat March 2026 ({datetime.now()})\nLat/Lon: {LAT}/{LON}\n\n"
    for entry in data_list:
        txt += f"\n=== {entry['type'].upper()} ===\n"
        txt += json.dumps(entry['raw'], indent=2)[:2000] + "\n..."
    
    with open("data/meteostat_march2026.txt", "w") as f:
        f.write(txt)
    logger.info("Saved data/meteostat_march2026.txt")
    
    return data_list

if __name__ == "__main__":
    result = fetch_meteostat_march2026()
    print("Check logs/meteostat_fetch.log & data/meteostat_march2026.txt")

