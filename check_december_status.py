#!/usr/bin/env python3
"""Check current data status in database"""

import psycopg2

conn = psycopg2.connect(
    dbname='energy_db',
    user='postgres',
    password='PdM',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

# Check date range for each source
print('=== Date Range by Source ===')
cur.execute('''
    SELECT source, MIN(timestamp) as min_date, MAX(timestamp) as max_date, COUNT(*) as cnt
    FROM sensor_data 
    GROUP BY source 
    ORDER BY source
''')
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} to {row[2]} ({row[3]} rows)')

# Check December 2025 data
print('\n=== December 2025 Check ===')
cur.execute("""
    SELECT COUNT(*) FROM sensor_data 
    WHERE timestamp >= '2025-12-01' AND timestamp < '2026-01-01'
""")
dec_count = cur.fetchone()[0]
print(f'December 2025 rows: {dec_count}')

# Check hourly coverage for December 2025
print('\n=== December 2025 Hourly Coverage by Source ===')
cur.execute("""
    SELECT source, COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours
    FROM sensor_data 
    WHERE timestamp >= '2025-12-01' AND timestamp < '2026-01-01'
    GROUP BY source
    ORDER BY source
""")
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} distinct hours')

conn.close()
