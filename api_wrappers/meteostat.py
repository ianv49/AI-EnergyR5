import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("ingestion_logger")

# RapidAPI Meteostat (500 req/month)
RAPIDAPI_HOST = "meteostat.p.rapidapi.com"
RAPIDAPI_KEY = "8e71ca59demsh1b87e385d8d80c4p1fb17djsnedd585a128aa"
LATITUDE = 14.5995  # Manila
LONGITUDE = 120.9842

def get_meteostat_data(start=None, end=None, hourly=True):
    """Fetch real hourly/daily Meteostat via RapidAPI. Logs to ingestion.log. None on fail."""
    try:
        url = "https://meteostat.p.rapidapi.com/point/hourly" if hourly else "https://meteostat.p.rapidapi.com/point/daily"
        start = start or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        end = end or datetime.now().strftime("%Y-%m-%d")

        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {"lat": LATITUDE, "lon": LONGITUDE, "start": start, "end": end}

        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
        response.raise_for_status()

        api_data = response.json()
        if "data" not in api_data or not api_data["data"]:
            logger.warning("Meteostat: no data")
            return None

        record = api_data["data"][-1]
        ts = record.get("time") or datetime.now().strftime("%Y-%m-%d %H:00:00")
        temp = record.get("temp")
        rh = record.get("rh")
        wind = record.get("wspd") or record.get("wind_speed")
        cloud = record.get("cloud_cover") or record.get("cldc")
        shortwave = record.get("shortwave_rad") or record.get("tsr")

        if all(x is not None for x in [temp, rh, wind, cloud, shortwave]):
            logger.info(f"Meteostat OK: {ts} temp={temp}")
            return ts, temp, rh, wind, cloud, shortwave

        logger.warning("Meteostat missing fields")
        return None

    except requests.exceptions.Timeout:
        logger.error("Meteostat timeout")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Meteostat HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"Meteostat: {e}")
        return None

if __name__ == "__main__":
    data = get_meteostat_data()
    print(data or "No real data (check logs/ingestion.log)")

