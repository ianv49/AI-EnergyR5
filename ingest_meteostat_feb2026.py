#!/usr/bin/env python3
"""
Ingest data/meteostat_feb2026.txt → DB (Feb 2026 scope).
Hourly: time/temp/rhum/wspd/coco → timestamp/temperature/humidity/wind_speed/source.
Irradiance/wpd/sey NULL. source='meteostat'. ~672 rows expected.
"""
import re
import logging
from db.db_connector import get_connection
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meteostat_ingest_feb")

def ingest_feb2026():
    """Parse hourly Feb 2026 txt, insert DB matching fields. Real web sensor data."""
    with open('data/meteostat_feb2026.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract hourly records (time/temp/rhum/wspd/coco)
    hourly = re.findall(r'"time":\s*"([^"]+)"[^}]*"temp":\s*([\d.-]+)[^}]*"rhum":\s*([\d.-]+)[^}]*"wspd":\s*([\d.-]+)[^}]*"coco":\s*(\d+)', content, re.DOTALL)
    
    if not hourly:
        logger.error("No hourly records found in data/meteostat_feb2026.txt")
        return 0

    logger.info(f"Found {len(hourly)} hourly records for ingest")

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for ts_str, temp_str, rhum_str, wspd_str, coco_str in hourly:
        temp = float(temp_str)
        humidity = float(rhum_str)
        wind_speed = float(wspd_str) / 3.6  # km/h → m/s
        cloudiness = int(coco_str) * 12.5   # 0-8 → 0-100%

        query = """
        INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, source)
        VALUES (%s, %s, %s, %s, 'meteostat')
        ON CONFLICT (timestamp, source) DO NOTHING
        """
        cur.execute(query, (ts_str, temp, humidity, wind_speed))
        if cur.rowcount:
            inserted += 1
            logger.info(f"Inserted {ts_str}: T={temp:.1f}°C H={humidity:.0f}% W={wind_speed:.1f}m/s C={cloudiness}%")

    conn.commit()
    
    # Summary stats
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source='meteostat'")
    total_meteostat = cur.fetchone()[0]
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source='meteostat'")
    date_range = cur.fetchone()
    
    logger.info(f"Feb ingest complete: {inserted} new rows. Total meteostat: {total_meteostat}")
    logger.info(f"Meteostat range: {date_range[0]} → {date_range[1]}")

    cur.close()
    conn.close()
    
    print(tabulate([
        ["New inserted (Feb)", inserted],
        ["Total meteostat", total_meteostat],
        ["Date range", f"{date_range[0]} → {date_range[1] if date_range[1] else 'N/A'}"]
    ], tablefmt="grid"))
    print("✅ Validate: py db/test_connection.py | py check_latest_dates.py")
    return inserted

if __name__ == "__main__":
    ingest_feb2026()

