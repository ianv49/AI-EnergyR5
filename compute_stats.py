#!/usr/bin/env python3
import os

# Read the collect1.txt file and parse data
data_file = r"data\collect1.txt"

wind_values = []
solar_values = []
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
                # Column 8 is wind_power_density (index 7), Column 9 is solar_energy_yield (index 8)
                wind_str = parts[7].strip()
                solar_str = parts[8].strip()
                
                # Skip if values are empty
                if wind_str and solar_str:
                    wind_val = float(wind_str)
                    solar_val = float(solar_str)
                    wind_values.append(wind_val)
                    solar_values.append(solar_val)
                    row_count += 1
        except (ValueError, IndexError):
            # Skip rows with parsing errors
            pass

# Calculate statistics
if wind_values:
    wind_min = min(wind_values)
    wind_max = max(wind_values)
    wind_mean = sum(wind_values) / len(wind_values)
else:
    wind_min = wind_max = wind_mean = 0

if solar_values:
    solar_min = min(solar_values)
    solar_max = max(solar_values)
    solar_mean = sum(solar_values) / len(solar_values)
else:
    solar_min = solar_max = solar_mean = 0

print(f"Total data rows: {row_count}")
print(f"Wind - Min: {wind_min:.2f}, Max: {wind_max:.2f}, Mean: {wind_mean:.2f}")
print(f"Solar - Min: {solar_min:.2f}, Max: {solar_max:.2f}, Mean: {solar_mean:.2f}")

# Save stats to a file for use in HTML generation
with open("stats.txt", 'w') as f:
    f.write(f"{row_count}\n{wind_min:.2f}\n{wind_max:.2f}\n{wind_mean:.2f}\n")
    f.write(f"{solar_min:.2f}\n{solar_max:.2f}\n{solar_mean:.2f}\n")
