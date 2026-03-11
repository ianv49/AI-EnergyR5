#!/usr/bin/env python3
"""Check Solcast February 2026 data in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check all sources for Feb 2026
cur.execute("""
    SELECT source, COUNT(*) 
    FROM sensor_data 
    WHERE timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
    GROUP BY source
""")
print("February 2026 data by source:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

# Check Solcast specifically
cur.execute("""
    SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
    FROM sensor_data 
    WHERE source = 'solcast' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
""")
row = cur.fetchone()
print(f"\nSolcast Feb 2026: {row[0]} rows")
if row[0] > 0:
    print(f"Date range: {row[1]} to {row[2]}")

conn.close()
