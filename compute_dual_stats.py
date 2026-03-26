#!/usr/bin/env python3
"""
Compute statistics for collect1.txt (sim), collect2.txt (nasa_power), collect3.txt (open_meteo), collect5.txt (meteostat), and collect7.txt (weatherbit)
"""

import csv
import json
from pathlib import Path

def compute_stats_for_file(filepath):
    """Compute min, max, mean for all numeric fields in a CSV file"""
    data = []
    with open(filepath, 'r') as f:
        # Skip comment lines
        lines = f.readlines()
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('id,'):
                start_idx = i
                break

        # Read CSV from the header line
        reader = csv.DictReader(lines[start_idx:])
        for row in reader:
            try:
                data.append({
                    'temperature': float(row['temperature']) if row['temperature'] else 0.0,
                    'humidity': float(row['humidity']) if row['humidity'] else 0.0,
                    'irradiance': float(row['irradiance']) if row['irradiance'] else 0.0,
                    'wind_speed': float(row['wind_speed']) if row['wind_speed'] else 0.0,
                    'wind_power_density': float(row['wind_power_density']) if row['wind_power_density'] else 0.0,
                    'solar_energy_yield': float(row['solar_energy_yield']) if row['solar_energy_yield'] else 0.0
                })
            except (ValueError, KeyError):
                # Skip malformed rows
                continue

    if not data:
        return None

    # Compute stats
    fields = ['temperature', 'humidity', 'irradiance', 'wind_speed', 'wind_power_density', 'solar_energy_yield']
    stats = {}

    for field in fields:
        values = [row[field] for row in data]
        stats[field] = {
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'count': len(values)
        }

    return stats

def main():
    data_dir = Path('data')
    collect1_path = data_dir / 'collect1.txt'
    collect2_path = data_dir / 'collect2.txt'
    collect3_path = data_dir / 'collect3.txt'
    collect5_path = data_dir / 'collect5.txt'

    results = {}

    # Process collect1.txt (sim API)
    if collect1_path.exists():
        print("Processing collect1.txt (sim API)...")
        sim_stats = compute_stats_for_file(collect1_path)
        if sim_stats:
            results['sim'] = sim_stats
            print(f"  Found {sim_stats['temperature']['count']} records")

    # Process collect2.txt (nasa_power API)
    if collect2_path.exists():
        print("Processing collect2.txt (nasa_power API)...")
        nasa_stats = compute_stats_for_file(collect2_path)
        if nasa_stats:
            results['nasa_power'] = nasa_stats
            print(f"  Found {nasa_stats['temperature']['count']} records")

    # Process collect3.txt (open_meteo API)
    if collect3_path.exists():
        print("Processing collect3.txt (open_meteo API)...")
        open_meteo_stats = compute_stats_for_file(collect3_path)
        if open_meteo_stats:
            results['open_meteo'] = open_meteo_stats
            print(f"  Found {open_meteo_stats['temperature']['count']} records")

    # Process collect5.txt (meteostat API)
    if collect5_path.exists():
        print("Processing collect5.txt (meteostat API)...")
        meteostat_stats = compute_stats_for_file(collect5_path)
        if meteostat_stats:
            results['meteostat'] = meteostat_stats
            print(f"  Found {meteostat_stats['temperature']['count']} records")

    # Output results
    print("\n=== STATISTICS SUMMARY ===")
    for api_name, stats in results.items():
        print(f"\n{api_name.upper()} API:")
        print(f"  Total Records: {stats['temperature']['count']}")
        for field, field_stats in stats.items():
            print(f"  {field}: min={field_stats['min']:.2f}, max={field_stats['max']:.2f}, mean={field_stats['mean']:.2f}")

    # Save to JSON for HTML use
    with open('api_stats.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nStatistics saved to api_stats.json")

if __name__ == '__main__':
    main()