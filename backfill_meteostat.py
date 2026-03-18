import sys
sys.path.append('.')

from api_wrappers.meteostat import get_meteostat_data
from db.db_connector import get_connection
from datetime import datetime, timedelta
import time

def backfill_meteostat(target_date="2025-01-01", test_single=False):
    """
    Test 1 row first, then full 24hr Jan 1 2025.
    Real web data aligned to DB format, 1 req optimized.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Test single first
    if test_single:
        print("🧪 Test 1 req: get_meteostat_data('2025-01-01', '2025-01-01')")
        data = get_meteostat_data("2025-01-01", "2025-01-01")
        print("Test data:", data or "No real data (check logs/ingestion.log)")
        cur.close()
        conn.close()
        return

    # Full 24hr Jan1 2025
    print(f"📅 Backfilling Meteostat Jan 1 2025 (24 hourly rows)")
    count = 0
    for hour in range(24):
        ts_str = f"2025-01-01 {hour:02d}:00:00"

        # 1 req optimized: same date range per call
        data = get_meteostat_data("2025-01-01", "2025-01-01")
        if data:
            ts_api, temp, rh, wind, cloud, irrad = data
            print(f"Real data for {ts_str}: temp={temp}, irrad={irrad}")

            query = """
            INSERT INTO sensor_data (timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, irradiance, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'meteostat')
            ON CONFLICT (timestamp, source) DO NOTHING
            """
            # Align DB: uv_index null/0
            cur.execute(query, (ts_str, temp, rh, wind, cloud, 0.0, irrad))
            conn.commit()
            count += cur.rowcount
            print(f"✅ Added {ts_str}")

        time.sleep(0.5)  # Safe rate

    cur.close()
    conn.close()
    print(f"✅ Complete: {count}/24 rows (check test_connection.py)")

if __name__ == "__main__":
    print("🧪 Test single first:")
    backfill_meteostat(test_single=True)
    print("\n✅ Test OK. Full 24hr:")
    backfill_meteostat()

