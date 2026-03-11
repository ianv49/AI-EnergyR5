#!/usr/bin/env python3
"""
Solcast Backfill for February 2026
Fetches solar irradiance data from Solcast API
Follows the same pattern as backfill_nasa_december_2025.py
"""

import sys
import os
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Solcast API parameters - use correct historic radiation_and_weather endpoint
SOLCAST_HISTORICAL_URL = "https://api.solcast.com.au/data/historic/radiation_and_weather"
LATITUDE = 14.5995
LONGITUDE = 120.9842

# Set your Solcast API key here
# Get free API key at: https://solcast.com/
API_KEY = "rg2rHnb5ZBCoYozZ_ET5I92XDDQpq_s8"


def fetch_solcast_historical(target_date):
    """Fetch historical solar data from Solcast API for a specific date"""
    try:
        # Use ISO 8601 datetime format for start and end
        start_str = target_date.strftime("%Y-%m-%dT00:00:00Z")
        # End date is the next day to get full 24 hours
        end_str = (target_date + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start": start_str,
            "end": end_str,
            "api_key": API_KEY,
            "format": "json"
        }
        
        # Pass API key as query parameter
        response = requests.get(SOLCAST_HISTORICAL_URL, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        hourly_data = []
        # Solcast returns data in "estimated_actuals" array with 30-minute intervals
        if "estimated_actuals" in data:
            for record in data["estimated_actuals"]:
                period_end = record.get("period_end", "")
                
                # Parse the timestamp - extract hour
                if period_end:
                    # period_end format: "2026-02-01T00:30:00+00:00"
                    # Extract just the datetime part
                    ts = period_end.replace("+00:00", "Z")
                    
                    # Get values
                    ghi = record.get("ghi", 0) or 0
                    dni = record.get("dni", 0) or 0
                    air_temp = record.get("air_temp", 28) or 28
                    
                    # Calculate DHI (approximate)
                    dhi = max(0, ghi - dni * 0.3) if dni > 0 else ghi * 0.3
                    
                    hourly_data.append({
                        "timestamp": ts,
                        "irradiance": ghi,
                        "ghi": ghi,
                        "dni": dni,
                        "dhi": round(dhi, 2),
                        "temperature": air_temp
                    })
        
        if hourly_data:
            logger.info(f"  API success: {target_date.date()} - {len(hourly_data)} records")
            return hourly_data
        
        logger.error(f"  API returned no data for {target_date.date()}")
        return None
        
    except Exception as e:
        logger.error(f"API error for {target_date}: {e}")
        return None


def get_simulated_hourly_data(target_date):
    """Generate simulated hourly solar data when API is not available"""
    hourly_data = []
    
    for hour in range(24):
        # Manila tropical climate simulation
        # Temperature peaks around 2-3 PM
        base_temp = 26 + 4 * (1 - abs(14 - hour) / 12)
        
        # Humidity higher at night
        if hour >= 18 or hour <= 6:
            base_humidity = 80
        else:
            base_humidity = 70
        
        # Wind speed
        wind_speed = 2.0 + (hour % 3) * 0.5
        
        # Irradiance based on time of day ( Manila)
        if 6 <= hour <= 18:
            hour_factor = 1 - abs(12 - hour) / 6
            ghi = 800 * hour_factor
            dni = ghi * 1.2 if 7 <= hour <= 17 else 0
            dhi = ghi * 0.3
        else:
            ghi = 0
            dni = 0
            dhi = 0
        
        timestamp = datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0)
        
        hourly_data.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "irradiance": round(ghi, 2),
            "ghi": round(ghi, 2),
            "dni": round(dni, 2),
            "dhi": round(dhi, 2),
            "temperature": round(base_temp, 2),
            "humidity": round(base_humidity, 2),
            "wind_speed": round(wind_speed, 2)
        })
    
    return hourly_data


def delete_solcast_data_for_range(start_date, end_date, label="range"):
    """Delete existing Solcast data for specified range"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM sensor_data 
            WHERE source = 'solcast' 
            AND timestamp >= %s 
            AND timestamp < %s
        """, (start_date, end_date))
        deleted = cur.rowcount
        conn.commit()
    conn.close()
    logger.info(f"Deleted {deleted} existing records for {label}")
    return deleted


def insert_solcast_hourly_data(hourly_records):
    """Insert hourly Solcast data into database - 1 row per hour"""
    if not hourly_records:
        return 0
    
    conn = get_connection()
    inserted = 0
    skipped = 0
    
    with conn.cursor() as cur:
        for record in hourly_records:
            timestamp_str = record.get("timestamp")
            
            # Parse timestamp
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp = timestamp.replace(tzinfo=None)
            else:
                timestamp = timestamp_str
            
            irradiance = record.get("irradiance", 0) or 0
            temperature = record.get("temperature", 28)
            humidity = record.get("humidity", 75)
            wind_speed = record.get("wind_speed", 2.5)
            
            # Calculate derived values
            wind_power_density = round(0.5 * 1.225 * (wind_speed ** 3), 2)
            solar_energy_yield = round(irradiance / 1000, 3)
            
            # Use ON CONFLICT DO NOTHING to handle duplicates
            cur.execute("""
                INSERT INTO sensor_data (
                    timestamp, temperature, humidity, wind_speed,
                    irradiance, wind_power_density, solar_energy_yield, source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, source) DO NOTHING
            """, (
                timestamp, round(temperature, 2), round(humidity, 2), 
                round(wind_speed, 2), round(irradiance, 2), 
                wind_power_density, solar_energy_yield, 'solcast'
            ))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        
        conn.commit()
    
    conn.close()
    logger.info(f"Inserted {inserted} new records, skipped {skipped} duplicates")
    return inserted


def deduplicate_solcast_data():
    """Delete duplicates, keeping only 1 row per hour"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM sensor_data WHERE source = 'solcast'
        """)
        before = cur.fetchone()[0]
        
        cur.execute("""
            DELETE FROM sensor_data 
            WHERE id NOT IN (
                SELECT MIN(id) FROM sensor_data 
                GROUP BY DATE(timestamp), EXTRACT(HOUR FROM timestamp), source
            )
            AND source = 'solcast'
        """)
        
        cur.execute("""
            SELECT COUNT(*) FROM sensor_data WHERE source = 'solcast'
        """)
        after = cur.fetchone()[0]
        
        deleted = before - after
        conn.commit()
    conn.close()
    return deleted


def backfill_february_2026():
    """Backfill Solcast data for February 2026 - REAL DATA ONLY, no simulated data"""
    
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 3, 1)
    
    logger.info("="*60)
    logger.info("SOLCAST BACKFILL - FEBRUARY 2026")
    logger.info("="*60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Expected: 28 days x 24 hours = 672 hours")
    logger.info("MODE: REAL DATA ONLY - No simulated data will be used")
    
    # Check if API key is set
    if API_KEY == "your_solcast_api_key_here":
        logger.error("ERROR: API key not set! Cannot fetch real data.")
        logger.error("Please set your Solcast API key in this script")
        return
    
    # Step 1: Delete existing February 2026 data
    delete_solcast_data_for_range(start_date, end_date, "February 2026")
    
    # Step 2: Fetch data for each day - REAL DATA ONLY
    all_hourly_records = []
    current = start_date
    api_success = 0
    failed_dates = []  # Track failed dates for reporting
    
    logger.info("\n--- Fetching Solcast data (REAL API only) ---")
    while current < end_date:
        # Try to fetch from API
        hourly_data = fetch_solcast_historical(current)
        
        if hourly_data:
            all_hourly_records.extend(hourly_data)
            api_success += 1
            logger.info(f"  SUCCESS: {current.date()} - {len(hourly_data)} records")
        else:
            # Report gap - NO simulated data fallback
            logger.warning(f"  GAP: No data available for {current.date()} - API failed")
            failed_dates.append(current.date())
        
        current += timedelta(days=1)
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.2)
    
    # Report gaps
    logger.info(f"\n" + "="*60)
    logger.info("RESULTS SUMMARY")
    logger.info("="*60)
    logger.info(f"  - API success: {api_success} days")
    logger.info(f"  - Total hourly records: {len(all_hourly_records)}")
    
    if failed_dates:
        logger.warning(f"  - GAPS DETECTED: {len(failed_dates)} days without data")
        logger.warning(f"    Failed dates: {[str(d) for d in failed_dates]}")
    else:
        logger.info("  - No gaps detected - all days fetched successfully")
    
    # Step 3: Insert all data at once (optimized - single batch)
    if all_hourly_records:
        logger.info("\n--- Inserting hourly data (single batch) ---")
        inserted = insert_solcast_hourly_data(all_hourly_records)
        logger.info(f"Inserted {inserted} records")
    else:
        logger.warning("\n--- No data to insert ---")
        inserted = 0
    
    logger.info("\n" + "="*60)
    logger.info("SOLCAST FEBRUARY 2026 BACKFILL COMPLETE")
    logger.info("="*60)
    logger.info(f"Total records inserted: {inserted}")
    
    # Step 4: Deduplicate to ensure only 1 row per hour
    dup_deleted = deduplicate_solcast_data()
    logger.info(f"Deduplication: Removed {dup_deleted} duplicate records")
    
    # Step 5: Verify and show summary
    verify_coverage()
    
    # Final gap report
    if failed_dates:
        logger.error("\n" + "="*60)
        logger.error("GAP REPORT - Data not available from Solcast API:")
        logger.error("="*60)
        for date in failed_dates:
            logger.error(f"  - {date}")
        logger.error("\nTo fill these gaps, consider:")
        logger.error("  1. Upgrading to a paid Solcast API plan")
        logger.error("  2. Using an alternative API (NASA POWER, Open-Meteo)")
        logger.error("  3. Waiting for API quota to reset")


def verify_coverage():
    """Verify the final coverage for February 2026"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT source, COUNT(*) as cnt, MIN(timestamp), MAX(timestamp)
            FROM sensor_data 
            WHERE timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            GROUP BY source ORDER BY source
        """)
        
        print("\n" + "="*60)
        print("FEBRUARY 2026 DATA SUMMARY")
        print("="*60)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} rows ({row[2]} to {row[3]})")
        
        cur.execute("""
            SELECT 
                COUNT(DISTINCT DATE(timestamp)) as days,
                COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours,
                AVG(irradiance) as avg_irradiance,
                MIN(irradiance) as min_irradiance,
                MAX(irradiance) as max_irradiance
            FROM sensor_data 
            WHERE source = 'solcast' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
        """)
        row = cur.fetchone()
        if row and row[0]:
            print(f"\n  Solcast Details:")
            print(f"    - Unique days: {row[0]}")
            print(f"    - Unique hours: {row[1]}")
            print(f"    - Avg irradiance: {round(row[2], 2) if row[2] else 'N/A'} W/m²")
            print(f"    - Min irradiance: {row[3] if row[3] else 'N/A'} W/m²")
            print(f"    - Max irradiance: {row[4] if row[4] else 'N/A'} W/m²")
    
    show_solcast_monthly_summary()
    conn.close()


def show_solcast_monthly_summary():
    """Show Solcast data summary by month"""
    conn = get_connection()
    with conn.cursor() as cur:
        print("\n" + "="*60)
        print("SOLCAST MONTHLY SUMMARY (ALL MONTHS)")
        print("="*60)
        
        months = [
            ('2025-01-01', '2025-02-01', 'January'),
            ('2025-02-01', '2025-03-01', 'February'),
            ('2025-03-01', '2025-04-01', 'March'),
            ('2025-04-01', '2025-05-01', 'April'),
            ('2025-05-01', '2025-06-01', 'May'),
            ('2025-06-01', '2025-07-01', 'June'),
            ('2025-07-01', '2025-08-01', 'July'),
            ('2025-08-01', '2025-09-01', 'August'),
            ('2025-09-01', '2025-10-01', 'September'),
            ('2025-10-01', '2025-11-01', 'October'),
            ('2025-11-01', '2025-12-01', 'November'),
            ('2025-12-01', '2026-01-01', 'December'),
            ('2026-01-01', '2026-02-01', 'January'),
            ('2026-02-01', '2026-03-01', 'February'),
            ('2026-03-01', '2026-04-01', 'March'),
        ]
        
        for start, end, name in months:
            cur.execute("""
                SELECT COUNT(*), 
                       AVG(irradiance), MIN(irradiance), MAX(irradiance)
                FROM sensor_data 
                WHERE source = 'solcast' AND timestamp >= %s AND timestamp < %s
            """, (start, end))
            row = cur.fetchone()
            if row and row[0] and row[0] > 0:
                print(f"  {name:12s}: {row[0]:4d} records | Avg: {row[1]:6.1f} W/m² | Range: {row[2]:5.1f} - {row[3]:5.1f} W/m²")
            else:
                print(f"  {name:12s}:    0 records")
        
        cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'solcast'")
        total = cur.fetchone()[0]
        print(f"\n  {'TOTAL':12s}: {total:4d} records")
    
    conn.close()


if __name__ == "__main__":
    backfill_february_2026()

