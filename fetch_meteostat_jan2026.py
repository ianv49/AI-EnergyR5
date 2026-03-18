import meteostat
import json
import logging
from db.db_connector import get_connection
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, filename='logs/meteostat_jan.log', filemode='w')
logger = logging.getLogger('meteostat_jan')

LAT = 14.5995  # Manila
LON = 120.9842

def fetch_and_ingest_jan2026():
    """Fetch real hourly Meteostat Jan 2026 → data/meteostat_jan2026.txt → ingest DB source='meteostat'."""
    try:
        logger.info('Fetching Jan 2026 hourly Meteostat native (real data)')
        point = meteostat.Point(LAT, LON)
        data = point.hourly('2026-01-01', '2026-01-31').fetch()
        
        if data.empty:
            logger.error('No data fetched')
            return False
        
        logger.info(f'Fetched {len(data)} hourly rows Jan 2026')
        
        # Save raw JSON for ingest_txt compat
        hourly_data = data.reset_index().to_dict('records')
        txt_content = f"=== HOURLY ===\n{json.dumps({'data': hourly_data})}\n=== DAILY ==="
        with open('data/meteostat_jan2026.txt', 'w') as f:
            f.write(txt_content)
        logger.info('Saved data/meteostat_jan2026.txt')
        
        # Direct ingest (map fields)
        conn = get_connection()
        cur = conn.cursor()
        inserted = 0
        
        for _, row in data.iterrows():
            ts = row.name.strftime('%Y-%m-%d %H:00:00')
            temp = row.get('temp')
            humidity = row.get('rhum')  # rhum %
            wind_speed = row.get('wspd', 0) / 3.6 if row.get('wspd') else None  # km/h to m/s
            cloudiness = row.get('coco', 0) * (100 / 8) if row.get('coco') else None  # 0-8 code to %
            irradiance = row.get('rsds')  # if avail, else None
            uv_index = None
            wpd = None
            sey = None
            
            if temp is not None and humidity is not None and wind_speed is not None:
                query = """
                INSERT INTO sensor_data 
                (timestamp, temperature, humidity, wind_speed, cloudiness, irradiance, uv_index, wind_power_density, solar_energy_yield, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'meteostat')
                ON CONFLICT (timestamp, source) DO NOTHING
                """
                cur.execute(query, (ts, temp, humidity, wind_speed, cloudiness, irradiance, uv_index, wpd, sey))
                if cur.rowcount > 0:
                    inserted += 1
                    logger.info(f'Inserted {ts}: T={temp} H={humidity:.1f}% W={wind_speed:.2f}m/s Cld={cloudiness:.1f}%')
        
        conn.commit()
        logger.info(f'✅ Committed {inserted} new rows (dupes skipped)')
        print(f'Success: {inserted} Jan 2026 meteostat rows inserted. Check logs/meteostat_jan.log')
        print('Verify: py db/test_connection.py | grep meteostat')
        return True
        
    except Exception as e:
        logger.error(f'Error: {e}')
        print(f'Failed: {e}')
        return False

if __name__ == '__main__':
    fetch_and_ingest_jan2026()

