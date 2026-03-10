"""Check Open-Meteo 2025 data status."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check Oct 2025
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2025-10-01' AND timestamp < '2025-11-01'")
oct_count = cur.fetchone()[0]
print(f"Open-Meteo Oct 2025: {oct_count} rows")

# Check Nov 2025
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2025-11-01' AND timestamp < '2025-12-01'")
nov_count = cur.fetchone()[0]
print(f"Open-Meteo Nov 2025: {nov_count} rows")

# Check Dec 2025
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2025-12-01' AND timestamp < '2026-01-01'")
dec_count = cur.fetchone()[0]
print(f"Open-Meteo Dec 2025: {dec_count} rows")

# Get date range
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'open_meteo'")
range_result = cur.fetchone()
print(f"Date range: {range_result[0]} to {range_result[1]}")

conn.close()
