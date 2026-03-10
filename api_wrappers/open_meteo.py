import requests
from datetime import datetime, timedelta
import random

# Open-Meteo API parameters
BASE_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 14.5995  # Manila latitude
LONGITUDE = 120.9842  # Manila longitude

def get_weather_data(hourly=True):
    """
    Fetch current weather data from Open-Meteo API for Manila.
    Returns temperature, humidity, wind speed, and irradiance.
    """
    try:
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,global_tilted_irradiance" if hourly else None,
            "timezone": "Asia/Manila"
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract current weather
        current = data.get("current", {})
        temperature = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        
        # Get irradiance if available
        irradiance = 0
        if hourly and "hourly" in data:
            hourly_data = data["hourly"]
            if "global_tilted_irradiance" in hourly_data:
                irradiance_arr = hourly_data["global_tilted_irradiance"]
                if irradiance_arr and len(irradiance_arr) > 0:
                    irradiance = irradiance_arr[0] if irradiance_arr[0] is not None else 0

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "irradiance": irradiance
        }

    except Exception as e:
        print(f"Error fetching Open-Meteo data: {e}, using simulated data")
        return get_simulated_weather_data()

def get_historical_data(start_date, end_date):
    """
    Fetch historical weather data from Open-Meteo API for a date range.
    Returns list of hourly weather data.
    """
    weather_data_list = []
    current_date = start_date

    while current_date <= end_date:
        try:
            params = {
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d"),
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,global_tilted_irradiance",
                "timezone": "Asia/Manila"
            }

            response = requests.get(HISTORICAL_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract hourly data
            hourly_data = data.get("hourly", {})
            times = hourly_data.get("time", [])
            temperatures = hourly_data.get("temperature_2m", [])
            humidities = hourly_data.get("relative_humidity_2m", [])
            wind_speeds = hourly_data.get("wind_speed_10m", [])
            irradiance_arr = hourly_data.get("global_tilted_irradiance", [])

            for i in range(len(times)):
                timestamp = times[i] if i < len(times) else current_date.strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(timestamp, str) and len(timestamp) == 10:
                    timestamp = timestamp + ":00:00"
                
                temp = temperatures[i] if i < len(temperatures) else 0
                hum = humidities[i] if i < len(humidities) else 0
                wind = wind_speeds[i] if i < len(wind_speeds) else 0
                irr = irradiance_arr[i] if i < len(irradiance_arr) and irradiance_arr[i] is not None else 0

                weather_data_list.append({
                    "timestamp": timestamp,
                    "temperature": temp,
                    "humidity": hum,
                    "wind_speed": wind,
                    "irradiance": irr
                })

            print(f"Fetched {len(times)} hours for {current_date.strftime('%Y-%m-%d')}")
            current_date += timedelta(days=1)

        except Exception as e:
            print(f"Error fetching Open-Meteo historical data for {current_date}: {e}")
            # Use simulated data for this day
            weather_data_list.extend(get_simulated_day_data(current_date))
            current_date += timedelta(days=1)

    return weather_data_list

def get_simulated_weather_data():
    """
    Generate simulated weather data for Manila.
    Based on typical tropical weather patterns.
    """
    current_hour = datetime.now().hour
    
    # Base temperature (warm tropical climate)
    base_temp = 28 + random.uniform(-3, 3)
    
    # Humidity varies throughout the day
    base_humidity = 75 + random.uniform(-10, 10)
    
    # Wind speed
    wind_speed = random.uniform(1, 5)
    
    # Irradiance based on time of day
    if 6 <= current_hour <= 18:
        hour_factor = 1 - abs(12 - current_hour) / 6
        irradiance = 800 * hour_factor + random.uniform(-50, 50)
    else:
        irradiance = random.uniform(0, 10)
    
    irradiance = max(0, min(1200, irradiance))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": timestamp,
        "temperature": round(base_temp, 2),
        "humidity": round(base_humidity, 2),
        "wind_speed": round(wind_speed, 2),
        "irradiance": round(irradiance, 2)
    }

def get_simulated_day_data(date):
    """
    Generate simulated weather data for a full day (24 hours).
    """
    weather_data_list = []
    
    for hour in range(24):
        # Base temperature varies by hour
        base_temp = 26 + 4 * (1 - abs(12 - hour) / 12) + random.uniform(-1, 1)
        
        # Humidity is higher at night
        if hour >= 18 or hour <= 6:
            base_humidity = 80 + random.uniform(-5, 10)
        else:
            base_humidity = 70 + random.uniform(-5, 10)
        
        # Wind speed
        wind_speed = random.uniform(1.5, 4.5)
        
        # Irradiance based on time of day
        if 6 <= hour <= 18:
            hour_factor = 1 - abs(12 - hour) / 6
            irradiance = 800 * hour_factor + random.uniform(-30, 30)
        else:
            irradiance = random.uniform(0, 5)
        
        irradiance = max(0, min(1200, irradiance))
        
        timestamp = date.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        
        weather_data_list.append({
            "timestamp": timestamp,
            "temperature": round(base_temp, 2),
            "humidity": round(base_humidity, 2),
            "wind_speed": round(wind_speed, 2),
            "irradiance": round(irradiance, 2)
        })
    
    return weather_data_list

def calculate_wind_power_density(wind_speed):
    """
    Calculate wind power density (W/m²) from wind speed (m/s).
    Formula: 0.5 * ρ * v³ where ρ is air density (~1.225 kg/m³)
    """
    if wind_speed is None or wind_speed <= 0:
        return 0
    air_density = 1.225  # kg/m³ at sea level
    return 0.5 * air_density * (wind_speed ** 3)

def calculate_solar_energy_yield(irradiance):
    """
    Calculate solar energy yield (kWh) from irradiance (W/m²).
    Assuming 1 hour integration time.
    """
    if irradiance is None or irradiance <= 0:
        return 0
    # Convert W/m² to kWh (divide by 1000 for kW and assume 1 hour)
    return round(irradiance / 1000, 2)

if __name__ == "__main__":
    # Test current weather fetch
    print("Testing Open-Meteo API...")
    data = get_weather_data()
    if data:
        print(f"Temperature: {data['temperature']}°C")
        print(f"Humidity: {data['humidity']}%")
        print(f"Wind Speed: {data['wind_speed']} m/s")
        print(f"Irradiance: {data['irradiance']} W/m²")
    else:
        print("Failed to fetch weather data")

