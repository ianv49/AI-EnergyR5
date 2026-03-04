#!/usr/bin/env python3
"""Show database summary per month and clean duplicates"""

import psycopg2

conn = psycopg2.connect(
    dbname='energy_db',
    user='postgres',
    password='PdM',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

print("="*70)
print("DATABASE SUMMARY - ALL MONTHS (2025)")
print("="*70)

# Check all months
months = [
    ('2025-01-01', '2025-02-01', 'January 2025'),
    ('2025-02-01', '2025-03-01', 'February 2025'),
    ('2025-03-01', '2025-04-01', 'March 2025'),
    ('2025-04-01', '2025-05-01', 'April 2025'),
    ('2025-05-01', '2025-06-01', 'May 2025'),
    ('2025-06-01', '2025-07-01', 'June 2025'),
    ('2025-07-01', '2025-08-01', 'July 2025'),
    ('2025-08-01', '2025-09-01', 'August 2025'),
    ('2025-09-01', '2025-10-01', 'September 2025'),
    ('2025-10-01', '2025-11-01', 'October 2025'),
    ('2025-11-01', '2025-12-01', 'November 2025'),
    ('2025-12-01', '2026-01-01', 'December 2025'),
]

total_all = 0
for start, end, name in months:
    cur.execute("""
        SELECT source, COUNT(*) as cnt
        FROM sensor_data 
        WHERE timestamp >= %s AND timestamp < %s
        GROUP BY source ORDER BY source
    """, (start, end))
    
    rows = cur.fetchall()
    if rows:
        print(f"\n--- {name} ---")
        month_total = 0
        for row in rows:
            print(f"  {row[0]}: {row[1]} rows")
            month_total += row[1]
        print(f"  TOTAL: {month_total}")
        total_all += month_total

print(f"\n{'='*70}")
print(f"GRAND TOTAL: {total_all} records")
print("="*70)

# Delete duplicates - keep first record per hour
print("\n--- Cleaning Duplicates ---")
cur.execute("""
    SELECT source, COUNT(*) as total FROM sensor_data 
    GROUP BY source
""")
print("Before deduplication:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} records")

cur.execute("""
    DELETE FROM sensor_data WHERE id NOT IN (
        SELECT MIN(id) FROM sensor_data 
        GROUP BY DATE(timestamp), EXTRACT(HOUR FROM timestamp), source
    )
""")
deleted_dups = cur.rowcount
conn.commit()

cur.execute("""
    SELECT source, COUNT(*) as total FROM sensor_data 
    GROUP BY source
""")
print("\nAfter deduplication:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} records")

print(f"\nTotal duplicates deleted: {deleted_dups}")

# Show NASA POWER stats for January 2025
print("\n--- NASA POWER January 2025 Details ---")
cur.execute("""
    SELECT COUNT(*) as cnt, 
           MIN(timestamp), MAX(timestamp),
           AVG(irradiance), MIN(irradiance), MAX(irradiance)
    FROM sensor_data 
    WHERE source = 'nasa_power' 
    AND timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
""")
row = cur.fetchone()
print(f"  Records: {row[0]}")
print(f"  Date range: {row[1]} to {row[2]}")
print(f"  Avg irradiance: {row[3]:.2f} W/m²")
print(f"  Min irradiance: {row[4]:.2f} W/m²")
print(f"  Max irradiance: {row[5]:.2f} W/m²")

conn.close()
