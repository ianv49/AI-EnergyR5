"""Fetch Meteostat hourly historical data for all months in 2025 and mirror to collect5.txt.

This script uses the `meteostat` Python library (no API key required) to fetch
real historical hourly data for Manila (default). It stores the data in the
PostgreSQL `sensor_data` table (source='meteostat_2025') and then regenerates
`data/collect5.txt` using the same 9-field schema used by other collectN files.

Usage:
  python fetch_meteostat_2025.py
  python fetch_meteostat_2025.py --year 2025 --start-month 1 --end-month 12

Note: This fetches real Meteostat data (not simulated/random).
"""

from __future__ import annotations

import argparse
import ssl
from datetime import date, datetime, timedelta

# Workaround SSL issues in restricted environments (cert verify failures)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

import meteostat
from db.db_connector import get_connection


def calculate_wind_power_density(wind_speed_mps: float) -> float:
    air_density = 1.225  # kg/m^3
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Meteostat hourly historical data for Jan-Dec 2025 and mirror to collect5.txt."
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=14.5995,
        help="Latitude (default: Manila 14.5995)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=120.9842,
        help="Longitude (default: Manila 120.9842)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year to fetch (default: 2025)",
    )
    parser.add_argument(
        "--start-month",
        type=int,
        default=1,
        help="Starting month (1-12, default=1)",
    )
    parser.add_argument(
        "--end-month",
        type=int,
        default=12,
        help="Ending month (1-12, default=12)",
    )
    return parser.parse_args()


def fetch_monthly_data(lat: float, lon: float, start_date: date, end_date: date):
    """Fetch a single month of hourly Meteostat data."""
    point = meteostat.Point(lat, lon)
    df = meteostat.hourly(point, start_date, end_date).fetch()
    return df


def ingest_df(df, source: str = "meteostat_2025") -> int:
    """Insert DataFrame rows into sensor_data and return number of inserted rows."""
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for ts, row in df.iterrows():
        timestamp = ts.strftime("%Y-%m-%d %H:00:00")
        temp = row.get("temp") or 0.0
        humidity = row.get("rh") or 0.0
        wind_kmh = row.get("wspd") or 0.0
        wind = float(wind_kmh) / 3.6

        irradiance = row.get("rsds") or 0.0
        # fall back to minutes of sunshine (tsun) if rsds not available
        if not irradiance:
            tsun = row.get("tsun")
            if tsun is not None:
                # rough conversion: 1 min sunshine ~ 10 W/m^2 (approx)
                irradiance = float(tsun) * 10.0

        wind_power_density = calculate_wind_power_density(wind)
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
            (
                timestamp,
                float(temp),
                float(humidity),
                float(irradiance),
                float(wind),
                source,
                float(wind_power_density),
                float(solar_energy_yield),
            ),
        )
        if cur.rowcount:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    return inserted


def main() -> None:
    args = parse_args()

    year = args.year
    start_month = max(1, min(12, args.start_month))
    end_month = max(1, min(12, args.end_month))
    if start_month > end_month:
        raise SystemExit("start-month must be <= end-month")

    total_inserted = 0
    for month in range(start_month, end_month + 1):
        start_date = date(year, month, 1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)

        print(f"Fetching {start_date} -> {end_date}...")
        try:
            df = fetch_monthly_data(args.lat, args.lon, start_date, end_date)
        except Exception as e:
            print(f"Failed to fetch {start_date} -> {end_date}: {e}")
            continue

        if df is None or df.empty:
            print(f"No data for {start_date} -> {end_date}")
            continue

        inserted = ingest_df(df, source="meteostat")
        total_inserted += inserted
        print(f"Inserted {inserted} rows for {month:02d}/{year}")

    # Regenerate collect5.txt from DB (9-field format)
    try:
        from generate_collect5_full import generate_full_collect5

        print("Regenerating data/collect5.txt...")
        generate_full_collect5()
    except Exception as e:
        print("Warning: Failed to regenerate collect5.txt:", e)

    print(f"✅ Done. Total inserted: {total_inserted}")


if __name__ == "__main__":
    main()
