#!/usr/bin/env python3
"""
Ingest data/meteostat_march2026.txt → DB.
Hourly: time/temp/rhum/wspd/coco → timestamp/temperature/humidity/wind_speed/source.
Leave irradiance/wpd/sey NULL. source='meteostat'.
"""
import re
import logging
from db.db_connector import get_connection
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meteostat_ingest")

def ingest_march2026():
    """Parse hourly, insert DB matching fields."""
    with open('data/meteostat_march2026.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Hourly records (reliable: time/temp/rhum/wspd/coco)
    hourly = re.findall(r'"time":\s*"([^"]+)"[^}]*"temp":\s*([\d.-]+)[^}]*"rhum":\s*([\d.-]+)[^}]*"wspd":\s*([\d.-]+)[^}]*"coco":\s*(\d+)', content)
    
    if not hourly:
        logger.error("No hourly records found")
        return 0

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for ts_str, temp_str, rhum_str, wspd_str, coco_str in hourly:
        temp = float(temp_str)
        humidity = float(rhum_str)
        wind_speed = float(wspd_str) / 3.6  # km/h → m/s
        # coco 0-8 → ignored (no DB field), log
        
        query = """
        INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, source)
        VALUES (%s, %s, %s, %s, 'meteostat')
        ON CONFLICT (timestamp, source) DO NOTHING
        """
        cur.execute(query, (ts_str, temp, humidity, wind_speed))
        if cur.rowcount:
            inserted += 1
            logger.info(f"Added {ts_str}: temp={temp:.1f} hum={humidity:.1f} wind={wind_speed:.1f}")

    conn.commit()
    # Summary
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source='meteostat'")
    total_meteostat = cur.fetchone()[0]
    logger.info(f"Total meteostat rows: {total_meteostat}")

    cur.close()
    conn.close()
    print(tabulate([["Inserted", inserted], ["Total meteostat", total_meteostat]], tablefmt="grid"))
    print("✅ Validate: py db/test_connection.py")
    return inserted

if __name__ == "__main__":
    ingest_march2026()

