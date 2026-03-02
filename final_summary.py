#!/usr/bin/env python3
"""Final data summary"""

import psycopg2

conn = psycopg2.connect(
    dbname='energy_db',
    user='postgres',
    password='PdM',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

print('='*60)
print('FINAL DATA SUMMARY')
print('='*60)

# Overall counts
cur.execute('SELECT source, COUNT(*) FROM sensor_data GROUP BY source ORDER BY source')
print('\nTotal Records by Source:')
total_all = 0
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]:,} rows')
    total_all += row[1]
print(f'  TOTAL: {total_all:,} rows')

# Monthly breakdown
print('\nRecords by Month:')
cur.execute("""
    SELECT 
        TO_CHAR(timestamp, 'YYYY-MM') as month,
        source,
        COUNT(*) as cnt
    FROM sensor_data 
    GROUP BY month, source
    ORDER BY month, source
""")
current_month = None
for row in cur.fetchall():
    if row[0] != current_month:
        current_month = row[0]
        print(f'\n{current_month}:')
    print(f'  {row[1]}: {row[2]} rows')

# Date range
print('\nDate Range by Source:')
cur.execute("""
    SELECT source, MIN(timestamp), MAX(timestamp)
    FROM sensor_data 
    GROUP BY source
    ORDER BY source
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} to {row[2]}')

conn.close()
