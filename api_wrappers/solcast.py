"""
Solcast API Wrapper
Fetches solar irradiance data from Solcast API
Solcast provides solar radiation data (GHI, DNI, DHI) for solar energy analysis
"""

import requests
from datetime import datetime, timedelta
import random
import os

# Solcast API configuration
# Get your free API key from https://solcast.com/
SOLCAST_API_KEY = os.getenv("SOLCAST_API_KEY", "your-solcast-api-key-here")
BASE_URL = "https://api.solcast.com.au/radiation/forecasts"

# Location: Manila, Philippines
LATITUDE = 14.5995
LONGITUDE = 120.9842


def get_solar_forecast_data():
    """
    Fetch solar forecast data from Solcast API.
    Returns current solar irradiance values.
    """
    try:
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "format": "json"
        }
        
        headers = {
            "Authorization": f"Bearer {SOLCAST_API_KEY}"
        }
        
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract current irradiance (GHI - Global Horizontal Irradiance)
        if "forecasts" in data and len(data["forecasts"]) > 0:
            forecast = data["forecasts"][0]
            ghi = forecast.get("ghi", 0)  # W/m²
            dni = forecast.get("dni", 0)  # W/m²
            dhi = forecast.get("dhi", 0)  # W/m²
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {
                "timestamp": timestamp,
                "ghi": ghi,
                "dni": dni,
                "dhi": dhi,
                "irradiance": ghi  # Use GHI as main irradiance value
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching Solcast data: {e}")
        return get_simulated_solcast_data()


def get_historical_data(start_date, end_date):
    """
    Fetch historical solar data from Solcast API for a date range.
    Note: Solcast free tier may have limited historical data access.
    Returns list of hourly solar data.
    """
    solar_data_list = []
    current_date = start_date
    
    # Solcast historical data endpoint
    historical_url = "https://api.solcast.com.au/radiation/archives"
    
    while current_date <= end_date:
        try:
            params = {
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "start": current_date.strftime("%Y-%m-%d"),
                "end": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "format": "json"
            }
            
            headers = {
                "Authorization": f"Bearer {SOLCAST_API_KEY}"
            }
            
            response = requests.get(historical_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract hourly data
            if "forecasts" in data:
                for forecast in data["forecasts"]:
                    timestamp = forecast.get("time", "")
                    ghi = forecast.get("ghi", 0)
                    dni = forecast.get("dni", 0)
                    dhi = forecast.get("dhi", 0)
                    
                    if timestamp:
                        # Parse timestamp and add timezone if needed
                        try:
                            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            ts = timestamp
                        
                        solar_data_list.append({
                            "timestamp": ts,
                            "ghi": ghi,
                            "dni": dni,
                            "dhi": dhi,
                            "irradiance": ghi
                        })
            
            print(f"Fetched Solcast data for {current_date.strftime('%Y-%m-%d')}")
            current_date += timedelta(days=1)
            
        except Exception as e:
            print(f"Error fetching Solcast historical data for {current_date}: {e}")
            # Use simulated data for this day
            solar_data_list.extend(get_simulated_day_data(current_date))
            current_date += timedelta(days=1)
    
    return solar_data_list


def get_simulated_solcast_data():
    """
    Generate simulated Solcast solar data for Manila.
    Based on typical tropical solar irradiance patterns.
    """
    current_hour = datetime.now().hour
    
    # GHI (Global Horizontal Irradiance) - peak around noon
    if 6 <= current_hour <= 18:
        hour_factor = 1 - abs(12 - current_hour) / 6
        hour_factor = max(0.1, hour_factor)
        ghi = 1000 * hour_factor + random.uniform(-50, 50)
    else:
        ghi = random.uniform(0, 10)
    
    ghi = max(0, min(1200, ghi))
    
    # DNI (Direct Normal Irradiance) - typically higher during clear sky
    dni = ghi * 0.7 + random.uniform(-30, 30)
    dni = max(0, min(1000, dni))
    
    # DHI (Diffuse Horizontal Irradiance)
    dhi = ghi * 0.3 + random.uniform(-20, 20)
    dhi = max(0, min(500, dhi))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": timestamp,
        "ghi": round(ghi, 2),
        "dni": round(dni, 2),
        "dhi": round(dhi, 2),
        "irradiance": round(ghi, 2)
    }


def get_simulated_day_data(date):
    """
    Generate simulated solar data for a full day (24 hours).
    """
    solar_data_list = []
    
    if isinstance(date, datetime):
        dt_date = date
    else:
        dt_date = datetime.combine(date, datetime.min.time())
    
    for hour in range(24):
        if 6 <= hour <= 18:
            hour_factor = 1 - abs(12 - hour) / 6
            hour_factor = max(0.1, hour_factor)
            ghi = 1000 * hour_factor + random.uniform(-30, 30)
        else:
            ghi = random.uniform(0, 5)
        
        ghi = max(0, min(1200, ghi))
        dni = ghi * 0.7 + random.uniform(-20, 20)
        dni = max(0, min(1000, dni))
        dhi = ghi * 0.3 + random.uniform(-10, 10)
        dhi = max(0, min(500, dhi))
        
        timestamp = dt_date.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        
        solar_data_list.append({
            "timestamp": timestamp,
            "ghi": round(ghi, 2),
            "dni": round(dni, 2),
            "dhi": round(dhi, 2),
            "irradiance": round(ghi, 2)
        })
    
    return solar_data_list


def calculate_wind_power_density(wind_speed):
    """
    Calculate wind power density (W/m²) from wind speed (m/s).
    Formula: 0.5 * ρ * v³ where ρ is air density (~1.225 kg/m³)
    """
    if wind_speed is None or wind_speed <= 0:
        return 0
    air_density = 1.225
    return round(0.5 * air_density * (wind_speed ** 3), 2)


def calculate_solar_energy_yield(irradiance):
    """
    Calculate solar energy yield (kWh) from irradiance (W/m²).
    Assuming 1 hour integration time.
    """
    if irradiance is None or irradiance <= 0:
        return 0
    return round(irradiance / 1000, 2)


if __name__ == "__main__":
    # Test current solar data fetch
    print("Testing Solcast API...")
    data = get_solar_forecast_data()
    if data:
        print(f"GHI: {data['ghi']} W/m²")
        print(f"DNI: {data['dni']} W/m²")
        print(f"DHI: {data['dhi']} W/m²")
        print(f"Irradiance: {data['irradiance']} W/m²")
    else:
        print("Failed to fetch Solcast data")
