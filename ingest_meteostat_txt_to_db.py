import json
import logging
from datetime import datetime
from db.db_connector import get_connection

logger = logging.getLogger("ingest_meteostat")

def ingest_meteostat_txt():
    """Parse meteostat_march2026.txt hourly → DB (direct/convert; blank others; source='meteostat')."""
    try:
        with open('data/meteostat_march2026.txt', 'r') as f:
            content = f.read()
        
        # Extract hourly data (JSON-like after === HOURLY ===)
        start_hourly = content.find('=== HOURLY ===') + len('=== HOURLY ===')
        json_str = content[start_hourly:].split('===')[0].strip()
        data = json.loads(json_str)
        
        hourly = data.get('data', [])
        logger.info(f"Parsing {len(hourly)} hourly records")
        
        conn = get_connection()
        cur = conn.cursor()
        inserted = 0
        
        for rec in hourly[:50]:  # Test first 50
            ts = rec['time']
            temp = rec.get('temp')
            humidity = rec.get('rhum')
            wind_speed = rec.get('wspd') / 3.6 if rec.get('wspd') else None  # km/h → m/s
            cloudiness = rec.get('coco', 0) * 17  # code 0-8 → 0-100% rough
            irradiance = None  # no rsds; tsun null
            uv_index = None  # no uv
            wpd = None  # calc later
            sey = None  # calc later
            
            if temp is not None and humidity is not None and wind_speed is not None:
                query = """
                INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'meteostat')
                ON CONFLICT (timestamp, source) DO NOTHING
                """
                cur.execute(query, (ts, temp, humidity, wind_speed, cloudiness, uv_index, irradiance))
                inserted += cur.rowcount
                logger.info(f"Inserted {ts}: temp={temp}, humidity={humidity}, wind={wind_speed}")
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Inserted {inserted} meteostat rows")
        print(f"Success: {inserted} rows. Validate: py db/test_connection.py")
        
    except Exception as e:
        logger.error(f"Ingest fail: {e}")

if __name__ == "__main__":
    ingest_meteostat_txt()

