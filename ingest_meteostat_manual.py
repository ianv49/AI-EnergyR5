#!/usr/bin/env python3
"""
Manual ingest: Parse first 10 hourly from data/meteostat_march2026.txt → DB.
Compatible: temp/rhum/wspd/coco → temp/humidity/wind_speed/cloudiness.
Blank others. source='meteostat'.
"""
import re
from datetime import datetime
from db.db_connector import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manual_ingest")

def manual_ingest():
    with open('data/meteostat_march2026.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract first 10 hourly records manually
    hourly_lines = re.findall(r'"time":\s*"([^"]+)"[^}]*"temp":\s*([\d.]+)[^}]*"rhum":\s*([\d.]+)[^}]*"wspd":\s*([\d.]+)[^}]*"coco":\s*(\d+)', content, re.MULTILINE)[:10]
    
    if not hourly_lines:
        logger.error("No matching records")
        return
    
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0
    
    for ts_str, temp_str, hum_str, wspd_str, coco_str in hourly_lines:
        temp = float(temp_str)
        humidity = float(hum_str)
        wind_speed = float(wspd_str) / 3.6  # km/h → m/s
        cloudiness = int(coco_str) * 12.5  # 0-8 → %
        
        query = """
        INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, source)
        VALUES (%s, %s, %s, %s, 'meteostat')
        ON CONFLICT (timestamp, source) DO NOTHING
        """
        cur.execute(query, (ts_str, temp, humidity, wind_speed))

        inserted += 1
        logger.info(f"Added {ts_str}: temp={temp} hum={humidity} wind={wind_speed:.1f} cloud={cloudiness}")
    
    conn.commit()
    conn.close()
    logger.info(f"✅ {inserted} meteostat rows in DB")
    print("Validate: py db/test_connection.py")

if __name__ == "__main__":
    manual_ingest()

