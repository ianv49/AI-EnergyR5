"""Print a summary of NOAA rows in sensor_data."""

import os
import sys

# Ensure project root (one level above this script) is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db.db_connector import get_connection

if __name__ == '__main__':
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM sensor_data;')
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source='noaa';")
    noaa = cur.fetchone()[0]

    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source='noaa';")
    rng = cur.fetchone()

    cur.execute(
        "SELECT timestamp, temperature, humidity, wind_speed, wind_power_density "
        "FROM sensor_data WHERE source='noaa' ORDER BY timestamp DESC LIMIT 5;"
    )
    rows = cur.fetchall()

    print(f'total_rows = {total}')
    print(f'noaa_rows = {noaa}')
    print(f'noaa_range = {rng}')
    print('sample_rows:')
    for r in rows:
        print(r)

    conn.close()
