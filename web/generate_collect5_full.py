import os
from db.db_connector import get_connection
from datetime import datetime

def generate_full_collect5():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source=%s", ('meteostat',))
    count = cur.fetchone()[0]
    
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source=%s", ('meteostat',))
    min_ts, max_ts = cur.fetchone()
    
    # All 678 rows ASC
    cur.execute("""
        SELECT rn, timestamp, COALESCE(temperature, 0), COALESCE(humidity, 0), COALESCE(wind_speed, 0), 
               COALESCE(cloudiness, 0), COALESCE(uv_index, 0), COALESCE(irradiance, 0), 
               COALESCE(wind_power_density, 0), COALESCE(solar_energy_yield, 0), source 
        FROM sensor_data WHERE source='meteostat' ORDER BY timestamp ASC
    """)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    header = '''# Full Meteostat DB mirror (678 rows)
# Generated: {}
# Summary: meteostat={} rows {} to {}

[meteostat]
id,timestamp,temperature,humidity,wind_speed,cloudiness,uv_index,irradiance,wind_power_density,solar_energy_yield,source'''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), count, min_ts, max_ts)
    
    csv_lines = []
    for row in rows:
        csv_lines.append(','.join(str(v or 0 if v is not None else '0') for v in row))
    
    content = header + '\\n' + '\\n'.join(csv_lines)
    
    path = '../data/collect5.txt'
    with open(path, 'w') as f:
        f.write(content)
    
    print(f'✅ Saved {count} meteostat rows to data/collect5.txt')
    return count

if __name__ == '__main__':
    generate_full_collect5()

