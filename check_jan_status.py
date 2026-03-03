#!/usr/bin/env python3
"""Quick check script for January 2025 data"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT source, COUNT(*) as cnt
    FROM sensor_data 
    WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
    GROUP BY source ORDER BY source
""")
print('January 2025 Data:')
total = 0
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} records')
    total += row[1]
print(f'  TOTAL: {total} records')

cur.execute("""
    SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data 
    WHERE source = 'nasa_power' AND timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
""")
result = cur.fetchone()
if result[0]:
    print(f'NASA POWER range: {result[0]} to {result[1]}')

