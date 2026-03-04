import psycopg2

conn = psycopg2.connect(
    dbname='energy_db',
    user='postgres',
    password='PdM',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

# March 2025 Coverage Summary
print('='*60)
print('NASA POWER BACKFILL - MARCH 2025 SUMMARY')
print('='*60)

cur.execute('''
    SELECT source, COUNT(*) as cnt, MIN(timestamp), MAX(timestamp)
    FROM sensor_data 
    WHERE timestamp >= '2025-03-01' AND timestamp < '2025-04-01'
    GROUP BY source ORDER BY source
''')
print('\n--- March 2025 Data Coverage ---')
total = 0
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} rows ({row[2]} to {row[3]})')
    total += row[1]
print(f'  TOTAL: {total} rows')

# NASA POWER details
cur.execute('''
    SELECT 
        COUNT(DISTINCT DATE(timestamp)) as days,
        COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours,
        AVG(irradiance) as avg_irr,
        MIN(irradiance) as min_irr,
        MAX(irradiance) as max_irr,
        AVG(temperature) as avg_temp,
        AVG(humidity) as avg_hum,
        AVG(wind_speed) as avg_wind
    FROM sensor_data 
    WHERE source = 'nasa_power' AND timestamp >= '2025-03-01' AND timestamp < '2025-04-01'
''')
row = cur.fetchone()
print(f'\n--- NASA POWER Details (Real Web Sensor Data) ---')
print(f'  Unique days: {row[0]}')
print(f'  Unique hours: {row[1]}')
print(f'  Avg irradiance: {round(row[2], 2)} kWh/m²/day')
print(f'  Min irradiance: {row[3]} kWh/m²/day')
print(f'  Max irradiance: {row[4]} kWh/m²/day')
print(f'  Avg temperature: {round(row[5], 1)} degC')
print(f'  Avg humidity: {round(row[6], 1)} %')
print(f'  Avg wind speed: {round(row[7], 1)} m/s')

# API data source verification
cur.execute('''
    SELECT COUNT(*) 
    FROM sensor_data 
    WHERE source = 'nasa_power' AND timestamp >= '2025-03-01' AND timestamp < '2025-04-01'
''')
print(f'\n--- Data Source ---')
print(f'  Source: NASA POWER API (power.larc.nasa.gov)')
print(f'  Location: Manila, Philippines (14.5995N, 120.9842E)')
print(f'  Parameter: ALLSKY_SFC_SW_DWN')
print(f'  Total records: {cur.fetchone()[0]}')

conn.close()
print('\n' + '='*60)
print('BACKFILL COMPLETE')
print('='*60)
