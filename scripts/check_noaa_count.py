"""Check how many NOAA rows currently exist in sensor_data."""

import os
import sys

# Ensure repo root is on the import path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db.db_connector import get_connection

if __name__ == '__main__':
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source='noaa';")
    count = cur.fetchone()[0]
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source='noaa';")
    rng = cur.fetchone()
    print('noaa_count=', count)
    print('noaa_range=', rng)
    conn.close()
