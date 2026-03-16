from datetime import datetime
from backfill_solcast_feb2026 import fetch_solcast_historical, insert_solcast_hourly_data
target = datetime(2026, 3, 1)
data = fetch_solcast_historical(target)
print('Fetched records:', len(data) if data else 0)
if data:
    inserted = insert_solcast_hourly_data(data)
    print('Inserted:', inserted)
from db.db_connector import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM sensor_data WHERE source = \'solcast\'')
total = cur.fetchone()[0]
print('Total solcast rows now:', total)
cur.execute('SELECT timestamp, irradiance, wind_speed, wind_power_density, solar_energy_yield FROM sensor_data WHERE source = \'solcast\' ORDER BY timestamp DESC LIMIT 5')
print('Latest 5 solcast rows:')
for row in cur.fetchall():
    print(row)
conn.close()
