#!/usr/bin/env python3
import os

# Read the collect1.txt file and parse data
data_file = r"data\collect1.txt"

# Initialize lists for each field
all_fields = {
    'temperature': [],
    'humidity': [],
    'irradiance': [],
    'wind_speed': [],
    'wind_power_density': [],
    'solar_energy_yield': []
}

row_count = 0

with open(data_file, 'r') as f:
    for line in f:
        line = line.strip()
        # Skip headers and comments
        if line.startswith('#') or line.startswith('[') or not line:
            continue
        if line.startswith('id,'):  # CSV header
            continue
        
        try:
            parts = line.split(',')
            if len(parts) >= 9:
                # Extract all fields
                # 2=temperature, 3=humidity, 4=irradiance, 5=wind_speed, 7=wind_power_density, 8=solar_energy_yield
                temp_str = parts[2].strip()
                humid_str = parts[3].strip()
                irrad_str = parts[4].strip()
                wind_spd_str = parts[5].strip()
                wind_pow_str = parts[7].strip()
                solar_str = parts[8].strip()
                
                # Skip if values are empty
                if all([temp_str, humid_str, irrad_str, wind_spd_str, wind_pow_str, solar_str]):
                    all_fields['temperature'].append(float(temp_str))
                    all_fields['humidity'].append(float(humid_str))
                    all_fields['irradiance'].append(float(irrad_str))
                    all_fields['wind_speed'].append(float(wind_spd_str))
                    all_fields['wind_power_density'].append(float(wind_pow_str))
                    all_fields['solar_energy_yield'].append(float(solar_str))
                    row_count += 1
        except (ValueError, IndexError):
            # Skip rows with parsing errors
            pass

print(f"Total data rows: {row_count}\n")

# Calculate and display statistics for each field
for field, values in all_fields.items():
    if values:
        min_val = min(values)
        max_val = max(values)
        mean_val = sum(values) / len(values)
        print(f"{field:25} - Min: {min_val:10.2f}, Max: {max_val:10.2f}, Mean: {mean_val:10.2f}")
    else:
        print(f"{field:25} - No data")

# Save stats to JSON format for easy consumption
import json

stats = {
    'total_rows': row_count,
    'fields': {}
}

for field, values in all_fields.items():
    if values:
        stats['fields'][field] = {
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'mean': round(sum(values) / len(values), 2)
        }

with open("stats.json", 'w') as f:
    json.dump(stats, f, indent=2)

print("\n✓ Statistics saved to stats.json")
