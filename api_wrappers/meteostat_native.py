import meteostat
from db.db_connector import get_connection
import logging
from datetime import datetime

logger = logging.getLogger("ingestion_logger")

def get_meteostat_native_data(lat=14.5995, lon=120.9842, start='2025-01-01', end='2025-01-01'):
    """Free Meteostat lib (no API key, cached). Hourly Jan1-2025 Manila."""
    try:
        data = meteostat.Point(lat, lon)  # Manila
        data = data.hourly(start, end)
        data = data.fetch()  # Cache
        
        if data.empty:
            logger.warning("Meteostat native: no data")
            return None
            
        # Latest row
        row = data.iloc[-1]
        ts = row.name.strftime("%Y-%m-%d %H:00:00")
        temp = row.get('temp', None)
        rh = row.get('rh', None)
        wind = row.get('wspd', None)  # km/h → m/s /3.6 if needed
        cloud = row.get('cldc', None)
        irrad = row.get('rsds', None) or row.get('tsun', None) / 60  # sunshine min → proxy
        
        if temp and rh and wind and cloud and irrad:
            logger.info(f"Meteostat native OK: {ts} temp={temp}")
            return ts, temp, rh, wind, cloud, irrad
        logger.warning(f"Missing fields: temp={temp} rh={rh} wind={wind} cloud={cloud} irrad={irrad}")
        return None

    except Exception as e:
        logger.error(f"Meteostat native: {e}")
        return None

if __name__ == "__main__":
    from backfill_meteostat import backfill_meteostat  # Reuse
    data = get_meteostat_native_data()
    print("Native test:", data)

