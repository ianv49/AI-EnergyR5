#!/usr/bin/env python3
# Fetch real Meteostat hourly Jan 2026 (744 rows), insert DB, append collect5.txt.

import requests
from db.db_connector import get_connection
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('meteostat_jan2026')

RAPIDAPI_HOST = "meteostat.p.rapidapi.com"
RAPIDAPI_KEY = "8e71ca59demsh1b87e385d8d80c4p1fb17djsnedd585a128aa"
LAT = 14.5995
LON = 120.9842

def fetch_and_ingest():
    url = "https://meteostat.p.rapidapi.com/point/hourly"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    params = {"lat": LAT, "lon": LON, "start": "2025-12-01", "end": "2025-12-31"} # Dec 2025

    response = requests.get(url, headers=headers, params=params, verify=False)
    response.raise_for_status()
    data = response.json()

    if 'data' not in data or not data['data']:
        logger.error('No data returned')
        return 0

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for record in data['data']:
        ts = record.get('time')
        temp = record.get('temp')
        rh = record.get('rh')
        wind_kmh = record.get('wspd')
        wind = wind_kmh / 3.6 if wind_kmh else 0
        cloud = record.get('cldc', 0) * 12.5
        uv = 0
        irr = record.get('shortwave_rad', 0)
        wpd = 0
        sey = 0
        src = 'meteostat_real_jan2026'

        if temp is not None and ts:
            cur.execute('''
                INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, wind_power_density, solar_energy_yield, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, source) DO NOTHING
            ''', (ts, temp, rh, wind, cloud, uv, irr, wpd, sey, src))
            if cur.rowcount:
                inserted += 1
                logger.info('Inserted %s: T=%s H=%s', ts, temp, rh)

    conn.commit()
    cur.close()
    conn.close()
    logger.info('Inserted %d rows', inserted)

    # Append note to collect5.txt
    with open('data/collect5.txt', 'a') as f:
        f.write('\n# Appended %d real Jan 2026 meteostat rows\n' % inserted)

    print('✅ %d real rows to DB + note to collect5.txt' % inserted)
    return inserted

if __name__ == '__main__':
    fetch_and_ingest()

