import re
import json
import logging
from datetime import datetime
from db.db_connector import get_connection

logger = logging.getLogger("ingest_meteostat_fixed")
logging.basicConfig(level=logging.INFO)

def parse_meteostat_txt():
    """Parse txt → clean JSON hourly data."""
    with open('data/meteostat_march2026.txt', 'r') as f:
        content = f.read()
    
    # Find hourly JSON block
    hourly_match = re.search(r'=== HOURLY ===\s*(\{.*?\})\s*(?====|$)', content, re.DOTALL)
    if not hourly_match:
        logger.error("No hourly JSON found")
        return []
    
    json_str = hourly_match.group(1)
    # Clean artifacts
    json_str = re.sub(r'null(?=\s*[,\}] )', 'null', json_str)
    json_str = re.sub(r'//.*', '', json_str)
    
    try:
        data = json.loads(json_str)
        return data.get('data', [])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse fail: {e}")
        logger.error(json_str[:500])
        return []

def ingest_hourly(hourly):
    """Save matching fields (temp/rhum/wspd/coco/tsun proxy); blank others."""
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0
    
    for rec in hourly[:24]:  # Test first day
        ts = rec['time']
        temp = rec.get('temp')
        humidity = rec.get('rhum')
        wind_speed = rec.get('wspd') / 3.6 if rec.get('wspd') else None  # km/h→m/s
        cloudiness = rec.get('coco', 0) * 12.5  # 0-8→0-100
        irradiance = rec.get('tsun') / 60 if rec.get('tsun') else None  # min→W/m² rough
        uv_index = None
        
        if temp is not None:
            query = """
            INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'meteostat')
            ON CONFLICT (timestamp, source) DO NOTHING
            """
            cur.execute(query, (ts, temp, humidity, wind_speed, cloudiness, uv_index, irradiance))
            inserted += cur.rowcount
            logger.info(f"{ts}: temp={temp} hum={humidity} wind={wind_speed} cloud={cloudiness} irr={irradiance}")
    
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"✅ {inserted} meteostat rows")
    return inserted

if __name__ == "__main__":
    hourly = parse_meteostat_txt()
    logger.info(f"Parsed {len(hourly)} records")
    count = ingest_hourly(hourly)
    print(f"Done: {count} saved. py db/test_connection.py")

