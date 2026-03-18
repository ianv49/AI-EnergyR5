import meteostat
import sys
sys.path.append('.')
from db.db_connector import get_connection
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion_logger")

def fetch_and_save_jan1_2025():
    """Test/fetch Jan1-2025 24hr, save DB."""
    try:
        point = meteostat.Point(14.5995, 120.9842)  # Manila
        data = point.hourly('2025-01-01', '2025-01-01').fetch()
        print("Raw data shape:", data.shape)
        print(data.head())
        
        if data.empty:
            print("No data")
            return

        conn = get_connection()
        cur = conn.cursor()
        count = 0
        
        for ts, row in data.iterrows():
            ts_str = ts.strftime("%Y-%m-%d %H:00:00")
            temp = row.get('temp', None)
            rh = row.get('rh', None)
            wind = row.get('wspd', None)
            cloud = row.get('cldc', None)
            irrad = row.get('rsds', None)  # surface solar rad
            
            if temp and rh and wind and cloud and irrad:
                query = """
                INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'meteostat_native')
                ON CONFLICT (timestamp, source) DO NOTHING
                """
                cur.execute(query, (ts_str, temp, rh, wind, cloud, 0.0, irrad))
                count += cur.rowcount
                print(f"Saved {ts_str}: temp={temp:.1f}, irrad={irrad:.1f}")
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Saved {count} rows meteostat_native")
        
    except Exception as e:
        logger.error(f"Meteostat native fetch: {e}")

if __name__ == "__main__":
    fetch_and_save_jan1_2025()

