"""Quick script to check Open-Meteo data in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check total open_meteo rows
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo'")
total = cur.fetchone()[0]
print(f"Total Open-Meteo rows: {total}")

# Check Feb 2026 data
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
feb_count = cur.fetchone()[0]
print(f"Feb 2026 Open-Meteo rows: {feb_count}")

# Check date range
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'open_meteo'")
date_range = cur.fetchone()
print(f"Date range: {date_range[0]} to {date_range[1]}")

conn.close()
