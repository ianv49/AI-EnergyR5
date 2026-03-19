"""Fetch Weatherbit hourly historical data for all months in 2025.

This script appends data to `data/collect7.txt` in the same 9-field format used by
collect1.txt (id,timestamp,temperature,humidity,irradiance,wind_speed,source,
wind_power_density,solar_energy_yield).

Usage:
  python fetch_weatherbit_2025.py --api-key <KEY>

If you want a different location, pass --lat/--lon.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import requests


def calculate_wind_power_density(wind_speed_mps: float) -> float:
    """Calculate wind power density (W/m^2) from wind speed (m/s)."""
    air_density = 1.225  # kg/m^3
    return round(0.5 * air_density * (wind_speed_mps ** 3), 2)


def calculate_solar_energy_yield(
    irradiance: float, cloudiness: float | None = None, uv_index: float | None = None
) -> float:
    """Estimate daily solar energy yield (kWh/m^2/day) from irradiance."""
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
        description="Fetch hourly Weatherbit historical data for Jan-Dec 2025."
    )
    parser.add_argument(
        "--api-key",
        help="Weatherbit API key (can also be set via WEATHERBIT_API_KEY env var)",
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
        "--output",
        default="data/collect7.txt",
        help="Output file path (default: data/collect7.txt)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting it",
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


def fetch_weatherbit_history(api_key: str, lat: float, lon: float, start: str, end: str) -> dict:
    """Fetch Weatherbit hourly history data."""

    url = "https://api.weatherbit.io/v2.0/history/hourly"

    params = {
        "lat": lat,
        "lon": lon,
        "start_date": f"{start}:00",
        "end_date": f"{end}:23",
        "key": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=60, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print("requests fetch failed, falling back to curl (-k):", exc)

    if shutil.which("curl") is None:
        raise SystemExit("Unable to fetch data: requests failed and curl was not found.")

    curl_cmd = [
        "curl",
        "-k",
        "-sS",
        "-G",
        url,
    ]
    for k, v in params.items():
        curl_cmd += ["--data-urlencode", f"{k}={v}"]

    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
    result.check_returncode()

    return json.loads(result.stdout)


def get_last_id(path: Path) -> int:
    if not path.exists():
        return 0
    last_id = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            parts = line.split(",", 1)
            try:
                last_id = int(parts[0])
            except Exception:
                continue
    return last_id


def write_rows(rows: list[dict], start_id: int, out_path: Path, append: bool) -> int:
    """Write rows to output file, returning the next start_id."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []

    if not append or not out_path.exists():
        lines.append(f"# Data collection last updated: {now}")
        lines.append(f"# Summary: weatherbit={len(rows)}")
        lines.append("[weatherbit]")
        lines.append(
            "id,timestamp,temperature,humidity,irradiance,wind_speed,source,wind_power_density,solar_energy_yield"
        )

    for idx, row in enumerate(rows, start=start_id):
        ts = (
            row.get("timestamp_utc")
            or row.get("timestamp_local")
            or row.get("ob_time")
            or ""
        )

        temperature = row.get("temp")
        humidity = row.get("rh")
        irradiance = row.get("solar_rad") or 0.0
        wind_speed = row.get("wind_spd")
        cloud_cover = row.get("clouds")
        uv_index = row.get("uv")

        temperature = 0.0 if temperature is None else temperature
        humidity = 0.0 if humidity is None else humidity
        irradiance = 0.0 if irradiance is None else irradiance
        wind_speed = 0.0 if wind_speed is None else wind_speed
        cloud_cover = 0.0 if cloud_cover is None else cloud_cover
        uv_index = None if uv_index is None else uv_index

        wind_power_density = calculate_wind_power_density(wind_speed)
        solar_energy_yield = calculate_solar_energy_yield(
            irradiance, cloud_cover, uv_index
        )

        lines.append(
            ",".join(
                [
                    str(idx),
                    ts,
                    f"{temperature:.2f}",
                    f"{humidity:.2f}",
                    f"{irradiance:.2f}",
                    f"{wind_speed:.2f}",
                    "weatherbit",
                    f"{wind_power_density:.2f}",
                    f"{solar_energy_yield:.3f}",
                ]
            )
        )

    mode = "a" if append and out_path.exists() else "w"
    with out_path.open(mode, encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return start_id + len(rows)


def main() -> None:
    args = parse_args()
    api_key = args.api_key or os.environ.get("WEATHERBIT_API_KEY")

    if not api_key:
        raise SystemExit("Missing Weatherbit API key; set WEATHERBIT_API_KEY or pass --api-key.")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    start_id = 1
    if args.append:
        start_id = get_last_id(out_path) + 1

    year = args.year
    start_month = max(1, min(12, args.start_month))
    end_month = max(1, min(12, args.end_month))

    if start_month > end_month:
        raise SystemExit("start-month must be <= end-month")

    # Loop month-by-month to avoid hitting API range limits
    for month in range(start_month, end_month + 1):
        start_date = datetime.date(year, month, 1)
        # last day of the month
        next_month = (start_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        end_date = next_month - datetime.timedelta(days=1)

        print(f"Fetching {start_date} -> {end_date}...")

        try:
            data = fetch_weatherbit_history(
                api_key, args.lat, args.lon, start_date.isoformat(), end_date.isoformat()
            )
            rows = data.get("data", [])
            if not rows:
                print(f"No data returned for {start_date} - {end_date}. Skipping.")
                continue

            start_id = write_rows(rows, start_id=start_id, out_path=out_path, append=args.append)
            # Once we have written at least one batch, ensure we append subsequent batches
            args.append = True

        except Exception as exc:
            print(f"Failed to fetch {start_date} - {end_date}: {exc}")
            raise

    print(f"Finished writing data to {out_path}")


if __name__ == "__main__":
    main()
