"""
Compare Feb 25-28 data across all sources
Check for consistency and anomalies
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime, date, timedelta

def check_feb25_28():
    """Check Feb 25-28 data for all sources"""
    conn = get_connection()
    
    print("="*70)
    print("FEBRUARY 25-28 DATA COMPARISON")
    print("="*70)
    
    # Get data for each source
    with conn.cursor() as cur:
        # OpenWeather data
        cur.execute("""
            SELECT timestamp, temperature, humidity, wind_speed, irradiance, 
                   wind_power_density, solar_energy_yield
            FROM sensor_data 
            WHERE source = 'openweather'
            AND timestamp >= '2026-02-25'
            AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        openweather = cur.fetchall()
        
        # NASA POWER data
        cur.execute("""
            SELECT timestamp, temperature, humidity, wind_speed, irradiance,
                   wind_power_density, solar_energy_yield
            FROM sensor_data 
            WHERE source = 'nasa_power'
            AND timestamp >= '2026-02-25'
            AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        nasa_power = cur.fetchall()
        
        # SIM data
        cur.execute("""
            SELECT timestamp, temperature, humidity, wind_speed, irradiance,
                   wind_power_density, solar_energy_yield
            FROM sensor_data 
            WHERE source = 'sim'
            AND timestamp >= '2026-02-25'
            AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        sim = cur.fetchall()
    
    conn.close()
    
    # Show counts
    print(f"\n📊 ROW COUNTS:")
    print(f"   OpenWeather: {len(openweather)} rows")
    print(f"   NASA_POWER: {len(nasa_power)} rows")
    print(f"   SIM: {len(sim)} rows")
    print(f"   Expected per source: 96 rows (4 days × 24 hours)")
    
    # Group by date
    def group_by_date(data):
        result = {}
        for row in data:
            dt = row[0].date()
            if dt not in result:
                result[dt] = []
            result[dt].append(row)
        return result
    
    ow_by_date = group_by_date(openweather)
    nasa_by_date = group_by_date(nasa_power)
    sim_by_date = group_by_date(sim)
    
    # Compare each day
    print(f"\n📅 DAY-BY-DAY COMPARISON:")
    print("-"*70)
    
    issues = []
    
    for day in range(25, 29):
        current_date = date(2026, 2, day)
        
        print(f"\n📆 {current_date} ({current_date.strftime('%A')})")
        
        ow_rows = ow_by_date.get(current_date, [])
        nasa_rows = nasa_by_date.get(current_date, [])
        sim_rows = sim_by_date.get(current_date, [])
        
        print(f"   OpenWeather: {len(ow_rows)}/24 | NASA_POWER: {len(nasa_rows)}/24 | SIM: {len(sim_rows)}/24")
        
        # Check for completeness
        if len(ow_rows) != 24:
            issues.append(f"{current_date}: OpenWeather has {len(ow_rows)} rows (expected 24)")
        if len(nasa_rows) != 24:
            issues.append(f"{current_date}: NASA_POWER has {len(nasa_rows)} rows (expected 24)")
        if len(sim_rows) != 24:
            issues.append(f"{current_date}: SIM has {len(sim_rows)} rows (expected 24)")
        
        # Show sample data from each source
        if ow_rows:
            sample = ow_rows[0]
            print(f"   🌤️  OpenWeather sample: temp={sample[1]}, humidity={sample[2]}, wind={sample[3]}")
        
        if nasa_rows:
            sample = nasa_rows[0]
            print(f"   ☀️  NASA_POWER sample: temp={sample[1]}, irradiance={sample[4]}")
        
        if sim_rows:
            sample = sim_rows[0]
            print(f"   🏭  SIM sample: temp={sample[1]}, humidity={sample[2]}, wind={sample[3]}")
    
    # Show timestamp overlap analysis
    print(f"\n🔍 TIMESTAMP OVERLAP ANALYSIS:")
    print("-"*70)
    
    # Get all timestamps for each source
    ow_timestamps = {row[0] for row in openweather}
    nasa_timestamps = {row[0] for row in nasa_power}
    sim_timestamps = {row[0] for row in sim}
    
    # Find common timestamps
    common_all = ow_timestamps & nasa_timestamps & sim_timestamps
    print(f"   Common timestamps (all 3 sources): {len(common_all)}")
    
    ow_only = ow_timestamps - nasa_timestamps - sim_timestamps
    nasa_only = nasa_timestamps - ow_timestamps - sim_timestamps
    sim_only = sim_timestamps - ow_timestamps - nasa_timestamps
    
    print(f"   OpenWeather-only timestamps: {len(ow_only)}")
    print(f"   NASA_POWER-only timestamps: {len(nasa_only)}")
    print(f"   SIM-only timestamps: {len(sim_only)}")
    
    if ow_only:
        print(f"\n   ⚠️  OpenWeather unique times: {sorted(ow_only)[:5]}...")
    if nasa_only:
        print(f"   ⚠️  NASA_POWER unique times: {sorted(nasa_only)[:5]}...")
    if sim_only:
        print(f"   ⚠️  SIM unique times: {sorted(sim_only)[:5]}...")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    
    if issues:
        print(f"⚠️  ISSUES FOUND: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No data completeness issues found!")
    
    print(f"\nTotal rows in Feb 25-28:")
    print(f"   OpenWeather: {len(openweather)}/96 ({100*len(openweather)/96:.1f}%)")
    print(f"   NASA_POWER: {len(nasa_power)}/96 ({100*len(nasa_power)/96:.1f}%)")
    print(f"   SIM: {len(sim)}/96 ({100*len(sim)/96:.1f}%)")

if __name__ == "__main__":
    check_feb25_28()
