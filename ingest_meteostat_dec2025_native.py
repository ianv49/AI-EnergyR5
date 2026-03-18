#!/usr/bin/env python3
"""
Ingest real historical Meteostat Dec 2025 hourly using native lib (no SSL/API key).
Save to DB source='meteostat_dec2025', mirror collect5.txt.
"""

import meteostat
from db.db_connector import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('meteostat_dec2025')

def ingest_dec2025():
    lat, lon = 14.5995, 120.9842  # Manila
    start = '2025-12-01'
    end = '2025-12-31'

    try:
        point = meteostat.Point(lat, lon)
        data = point.hourly(start, end).fetch()
        
        if data.empty:
            logger.warning('No data for Dec 2025')
            return 0

        logger.info(f'Fetched {len(data)} hourly rows Dec 2025')

        conn = get_connection()
        cur = conn.cursor()
        inserted = 0

        for ts, row in data.iterrows():
            timestamp = ts.strftime('%Y-%m-%d %H:00:00')
            temp = row.get('temp', 0)
            rh = row.get('rh', 0)
            wind_kmh = row.get('wspd', 0)
            wind = wind_kmh / 3.6
            cloud = row.get('cldc', 0) * 12.5
            uv = 0
            rsds = row.get('rsds', 0)  # Shortwave radiation
            wpd = 0
            sey = 0
            source = 'meteostat_dec2025_real'

            cur.execute('''
                INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, wind_power_density, solar_energy_yield, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (timestamp, temp, rh, wind, cloud, uv, rsds, wpd, sey, source))
            
            if cur.rowcount:
                inserted += 1
                logger.info('Inserted %s T=%.1f', timestamp, temp)

        conn.commit()
        cur.close()
        conn.close()

        # Mirror updated meteostat to collect5.txt
        import generate_collect5_full
        generate_collect5_full.generate_full_collect5()

        logger.info('Total inserted: %d, collect5.txt mirrored', inserted)
        print(f'✅ {inserted} Dec 2025 real rows to DB, collect5.txt updated ({generate_collect5_full.generate_full_collect5()})')
        return inserted

    except Exception as e:
        logger.error('Error: %s', e)
        return 0

if __name__ == '__main__':
    ingest_dec2025()

