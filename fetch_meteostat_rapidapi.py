"""Fetch Meteostat hourly data via RapidAPI and mirror to collect5.txt.

This script uses the Meteostat RapidAPI endpoint (point/hourly) to fetch historical
hourly weather data for Manila. It inserts the results into `sensor_data` and then
generates `data/collect5.txt` in the 9-field format.

Usage:
  python fetch_meteostat_rapidapi.py --year 2026 --months 1,3

Limits:
- RapidAPI free plan has request limits (500/month). This script makes one request per month.
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
import requests
from db.db_connector import get_connection


RAPIDAPI_HOST = "meteostat.p.rapidapi.com"
RAPIDAPI_KEY = "8e71ca59demsh1b87e385d8d80c4p1fb17djsnedd585a128aa"
LATITUDE = 14.5995
LONGITUDE = 120.9842


def calculate_wind_power_density(wind_speed_mps: float) -> float:
    air_density = 1.225
    return round(0.5 * air_density * (wind_speed_mps ** 3), 2)


def calculate_solar_energy_yield(
    irradiance: float, cloudiness: float | None = None, uv_index: float | None = None
) -> float:
    peak_sun_hours = 4.0
    cloud_factor = 1.0
    if cloudiness is not None:
        cloud_factor = max(0.0, min(1.0, (100.0 - cloudiness) / 100.0))

    uv_factor = 1.0
    if uv_index is not None:
        uv_factor = max(0.5, min(2.0, uv_index / 6.0))

    daily_yield = (irradiance * peak_sun_hours * cloud_factor * uv_factor) / 1000.0
    return round(daily_yield, 3)


def fetch_hourly(start: str, end: str) -> list[dict]:
    url = "https://meteostat.p.rapidapi.com/point/hourly"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "start": start,
        "end": end,
    }

    resp = requests.get(url, headers=headers, params=params, timeout=60, verify=False)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def ingest_records(records: list[dict], source: str = "meteostat") -> int:
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for rec in records:
        ts = rec.get("time")
        if not ts:
            continue

        temp = rec.get("temp") or 0.0
        humidity = rec.get("rhum") or 0.0
        wind_kmh = rec.get("wspd") or 0.0
        wind_speed = float(wind_kmh) / 3.6

        irradiance = rec.get("shortwave_rad") or 0.0
        if not irradiance:
            # Use sunshine minutes as rough proxy (if available)
            tsun = rec.get("tsun")
            if tsun is not None:
                irradiance = float(tsun) * 10.0

        wind_power_density = calculate_wind_power_density(wind_speed)
        solar_energy_yield = calculate_solar_energy_yield(irradiance)

        cur.execute(
            """
            INSERT INTO sensor_data (timestamp, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp, source) DO UPDATE
                SET temperature = EXCLUDED.temperature,
                    humidity = EXCLUDED.humidity,
                    irradiance = EXCLUDED.irradiance,
                    wind_speed = EXCLUDED.wind_speed,
                    wind_power_density = EXCLUDED.wind_power_density,
                    solar_energy_yield = EXCLUDED.solar_energy_yield;
            """,
            (ts, float(temp), float(humidity), float(irradiance), float(wind_speed), source, float(wind_power_density), float(solar_energy_yield)),
        )
        if cur.rowcount:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    return inserted


def parse_months(months_str: str | None) -> list[int]:
    """Parse a months string like "1,3" or "1-3" into a list of month numbers."""

    if not months_str:
        return list(range(1, 13))

    months: set[int] = set()
    for part in months_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            months.update(range(start, end + 1))
        else:
            months.add(int(part))

    return sorted(m for m in months if 1 <= m <= 12)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch hourly Meteostat data (via RapidAPI) and mirror it to data/collect5.txt."
    )
    parser.add_argument("--year", type=int, default=2025, help="Year to fetch (default: 2025)")
    parser.add_argument(
        "--months",
        type=str,
        default="1-12",
        help="Comma-separated months to fetch, e.g. 1,3, or a range like 1-3. Default is 1-12.",
    )
    args = parser.parse_args()

    year = args.year
    months = parse_months(args.months)

    total_inserted = 0

    for month in months:
        start_date = datetime.date(year, month, 1)
        # Last day of month
        next_month = (start_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        end_date = next_month - datetime.timedelta(days=1)

        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        print(f"Fetching {start_str} -> {end_str}...")
        try:
            records = fetch_hourly(start_str, end_str)
        except Exception as e:
            print(f"Failed to fetch {start_str} - {end_str}: {e}")
            continue

        inserted = ingest_records(records, source="meteostat")
        total_inserted += inserted
        print(f"Inserted {inserted} rows for {year}-{month:02d}")

        # throttle to avoid rate limits
        time.sleep(1)

    print("Regenerating data/collect5.txt...")
    try:
        from generate_collect5_full import generate_full_collect5

        generate_full_collect5()
    except Exception as e:
        print("Warning: failed to regenerate collect5.txt:", e)

    print(f"✅ Done; total inserted: {total_inserted}")


if __name__ == "__main__":
    main()
