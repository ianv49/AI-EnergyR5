import requests
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

# PVOutput API parameters
BASE_URL = "https://pvoutput.org/getsystem.jsp"
LATITUDE = 14.5995  # Manila latitude
LONGITUDE = 120.9842  # Manila longitude
import config
SYSTEM_ID = config.PVOUTPUT_SYSTEM_ID
API_KEY = config.PVOUTPUT_API_KEY

def fetch_pvoutput_daily(target_date):
    """
    Fetch daily data from PVOutput API for target date (REAL data only).
    Returns (date, avg_daily_irradiance, temperature) or raises ValueError if invalid/no data.
    Derives irr from Status v1 (0-12 sun% -> rough avg W/m2).
    """
    try:
        date_str = target_date.strftime("%Y%m%d")
        params = {
            "id": SYSTEM_ID,
            "key": API_KEY,
            "date": date_str
        }

        response = requests.get(BASE_URL, params=params, timeout=30, verify=False)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        status_elem = root.find('.//status')
        if status_elem is None or status_elem.text == '':
            raise ValueError("No status data")

        status_str = status_elem.text  # comma sep v1,v2,...,v6
        values = [v.strip() for v in status_str.split(',') if v.strip()]
        
        if len(values) < 2:
            raise ValueError("Invalid status format")

        sun_status = int(values[0])  # v1: 0=0%,1=10%,...,12=100+% sun
        temp_c = float(values[1]) if len(values) > 1 and values[1] else 28.0  # v5 temp fallback tropical

        # Derive avg daily irradiance: sun_status * 70 W/m2 (calib ~ tropical 5sun*1000h/24~200Wh avg)
        avg_daily_irr = sun_status * 70.0

        if avg_daily_irr > 0:
            print(f"PVOutput success: {target_date.date()} status={sun_status}, temp={temp_c}, irr={avg_daily_irr:.1f} W/m2")
            return (target_date, avg_daily_irr, temp_c)

        raise ValueError(f"Invalid PVOutput data: status={sun_status}, irr=0")

    except Exception as e:
        raise ValueError(f"Failed PVOutput API {target_date.date()}: {e}")

def get_realistic_hourly_irradiance(base_irr, hour, temp_c):
    """Convert daily avg irr to hourly (same as NASA: night0, peak noon)"""
    if hour < 6 or hour > 18:
        return 0.0
    
    hour_factor = 1 - abs(12 - hour) / 6.0
    hour_factor = max(0.1, hour_factor)
    
    # Variation based on hash for determinism
    var = (hash(f"{hour}{int(base_irr)}") % 20 - 10) / 100.0
    hourly = base_irr * hour_factor * (1 + var)
    return round(hourly, 2)

# Test
if __name__ == "__main__":
    # Test recent date (replace with past date for real test)
    test_date = datetime.now() - timedelta(days=1)
    try:
        data = fetch_pvoutput_daily(test_date)
        print(f"Fetched: {data}")
    except ValueError as e:
        print(f"Test failed (expected if no data): {e}")

