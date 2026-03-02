"""
Script to analyze February 2026 data coverage
Checks which dates and hours have data for each source
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime, date, timedelta
from collections import defaultdict

def check_february_coverage():
    """Check data coverage for February 2026"""
    conn = get_connection()
    
    # February 2026 has 28 days
    feb_start = date(2026, 2, 1)
    feb_end = date(2026, 2, 28)
    
    print("=" * 60)
    print("FEBRUARY 2026 DATA COVERAGE ANALYSIS")
    print("=" * 60)
    
    sources = ['openweather', 'nasa_power', 'sim']
    
    for source in sources:
        print(f"\n{'='*60}")
        print(f"Source: {source.upper()}")
        print(f"{'='*60}")
        
        with conn.cursor() as cur:
            # Get all timestamps for this source in February 2026
            cur.execute("""
                SELECT timestamp 
                FROM sensor_data 
                WHERE source = %s 
                AND timestamp >= %s 
                AND timestamp < %s
                ORDER BY timestamp
            """, (source, feb_start, feb_end + timedelta(days=1)))
            
            rows = cur.fetchall()
            
            if not rows:
                print("❌ NO DATA FOUND!")
                continue
            
            # Group by date
            data_by_date = defaultdict(set)
            for row in rows:
                ts = row[0]
                data_by_date[ts.date()].add(ts.hour)
            
            # Calculate stats
            total_rows = len(rows)
            dates_with_data = len(data_by_date)
            total_hours = sum(len(hours) for hours in data_by_date.values())
            expected_hours = 28 * 24  # 28 days * 24 hours
            
            print(f"Total rows: {total_rows}")
            print(f"Dates with data: {dates_with_data}/28")
            print(f"Total hours with data: {total_hours}/{expected_hours} ({100*total_hours/expected_hours:.1f}%)")
            
            # Check each date
            print(f"\nDate-by-date breakdown:")
            print("-" * 50)
            
            missing_dates = []
            incomplete_dates = []
            
            for day in range(1, 29):
                current_date = date(2026, 2, day)
                hours = data_by_date.get(current_date, set())
                
                if len(hours) == 0:
                    missing_dates.append(current_date)
                    print(f"  {current_date}: ❌ NO DATA")
                elif len(hours) < 24:
                    missing_hours = set(range(24)) - hours
                    incomplete_dates.append((current_date, sorted(missing_hours)))
                    print(f"  {current_date}: ⚠️  {len(hours)}/24 hours - Missing: {sorted(missing_hours)}")
                else:
                    print(f"  {current_date}: ✅ {len(hours)}/24 hours")
            
            if missing_dates:
                print(f"\n⚠️  MISSING DATES: {len(missing_dates)}")
                print(f"   {missing_dates}")
            
            if incomplete_dates:
                print(f"\n⚠️  INCOMPLETE DATES: {len(incomplete_dates)}")
                for d, h in incomplete_dates[:5]:  # Show first 5
                    print(f"   {d}: missing {len(h)} hours")
                if len(incomplete_dates) > 5:
                    print(f"   ... and {len(incomplete_dates) - 5} more")
    
    conn.close()
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_february_coverage()
