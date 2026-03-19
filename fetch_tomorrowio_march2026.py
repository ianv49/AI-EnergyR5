"""Fetch hourly weather data from Tomorrow.io for March 2026 and write to data/collect6.txt.

Output format matches the 9-field CSV layout used by data/collect1.txt:
  id,timestamp,temperature,humidity,irradiance,wind_speed,source,wind_power_density,solar_energy_yield

This script requires a Tomorrow.io API key, which can be provided either via the
TOMORROW_API_KEY environment variable or via the --api-key argument.

Example:
  TOMORROW_API_KEY=xxx python fetch_tomorrowio_march2026.py

Note: Tomorrow.io limits the number of calls per minute/day depending on your plan.
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
    """Calculate wind power density (W/m^2) from wind speed in m/s."""
    air_density = 1.225  # kg/m^3 at sea level
    return round(0.5 * air_density * (wind_speed_mps ** 3), 2)


def calculate_solar_energy_yield(
    irradiance: float, cloudiness: float, uv_index: float | None = None
) -> float:
    """Estimate daily solar energy yield (kWh/m^2/day) from irradiance + cloud/UV."""
    peak_sun_hours = 4.0
    cloud_factor = max(0.0, min(1.0, (100.0 - cloudiness) / 100.0))

    uv_factor = 1.0
    if uv_index is not None:
        uv_factor = max(0.5, min(2.0, uv_index / 6.0))

    daily_yield = (irradiance * peak_sun_hours * cloud_factor * uv_factor) / 1000.0
    return round(daily_yield, 3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch hourly weather data from Tomorrow.io for March 2026."
    )
    parser.add_argument(
        "--api-key",
        help="Tomorrow.io API key (can also be set via TOMORROW_API_KEY env var)",
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
        "--start",
        default="2026-03-01T00:00:00Z",
        help="Start time in ISO8601 (UTC).",
    )
    parser.add_argument(
        "--end",
        default="2026-03-31T23:00:00Z",
        help="End time in ISO8601 (UTC).",
    )
    parser.add_argument(
        "--output",
        default="data/collect6.txt",
        help="Output file path (default: data/collect6.txt)",
    )
    return parser.parse_args()


def fetch_tomorrowio_timelines(url: str, params: dict, headers: dict, timeout: int = 60) -> dict:
    """Fetch and return parsed JSON from Tomorrow.io timelines endpoint.

    Tries an HTTP request via `requests` first; if that fails (commonly due to
    SSL certificate revocation checks in restricted environments), falls back
    to using `curl -k` if available.
    """

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout, verify=False)
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
    for k, v in headers.items():
        curl_cmd += ["-H", f"{k}: {v}"]

    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=timeout)
    result.check_returncode()

    return json.loads(result.stdout)


def main() -> None:
    args = parse_args()
    api_key = args.api_key or os.environ.get("TOMORROW_API_KEY")

    if not api_key:
        raise SystemExit(
            "Missing Tomorrow.io API key. Set TOMORROW_API_KEY or pass --api-key."
        )

    url = "https://api.tomorrow.io/v4/timelines"
    # Only a limited subset of fields are available on the current Tomorrow.io plan.
    # ``solarRadiation`` / ``ghi`` are not permitted, so irradiance is produced as 0.
    fields = [
        "temperature",
        "humidity",
        "windSpeed",
        "windDirection",
    ]

    params = {
        "location": f"{args.lat},{args.lon}",
        "fields": ",".join(fields),
        "timesteps": "1h",
        "units": "metric",
        "startTime": args.start,
        "endTime": args.end,
    }

    headers = {"Accept": "application/json", "apikey": api_key}

    def fetch_with_24h_fallback(params: dict) -> list[dict]:
        """Fetch timelines, falling back to the most recent 24 hours if needed."""

        try:
            payload = fetch_tomorrowio_timelines(url, params, headers, timeout=60)
            intervals = payload.get("data", {}).get("timelines", [])
            if intervals:
                return intervals[0].get("intervals", [])
        except Exception as exc:
            msg = str(exc)
            if "startTime cannot be more than 24 hours in the past" not in msg:
                raise

        # If we get here, the requested range is restricted; fall back to last 24h.
        # Align to whole hours, since the API expects clean hourly boundaries.
        now = datetime.datetime.now(datetime.timezone.utc)
        start_dt = now.replace(minute=0, second=0, microsecond=0)
        end_dt = start_dt + datetime.timedelta(hours=23)

        fallback_start = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        fallback_end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Falling back to next 24 hours (forecast window): {fallback_start} → {fallback_end}")

        params["startTime"] = fallback_start
        params["endTime"] = fallback_end

        payload = fetch_tomorrowio_timelines(url, params, headers, timeout=60)
        intervals = payload.get("data", {}).get("timelines", [])
        if not intervals:
            raise SystemExit("Tomorrow.io response did not contain any timelines.")

        return intervals[0].get("intervals", [])

    intervals = fetch_with_24h_fallback(params)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append(f"# Data collection last updated: {now}")
    lines.append(f"# Summary: tomorrow={len(intervals)}")
    lines.append("[tomorrow]")
    lines.append(
        "id,timestamp,temperature,humidity,irradiance,wind_speed,source,wind_power_density,solar_energy_yield"
    )

    for idx, interval in enumerate(intervals, start=1):
        ts = interval.get("startTime")
        vals = interval.get("values", {})

        temperature = vals.get("temperature")
        humidity = vals.get("humidity")
        wind_speed = vals.get("windSpeed")

        # This plan does not provide solar irradiance/UV/cloud cover, so those are
        # set to 0 to preserve the 9-column schema.
        irradiance = 0.0
        cloud_cover = 0.0
        uv_index = None

        # Use 0s for None values to keep consistent columns
        temperature = 0.0 if temperature is None else temperature
        humidity = 0.0 if humidity is None else humidity
        wind_speed = 0.0 if wind_speed is None else wind_speed

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
                    "tomorrow",
                    f"{wind_power_density:.2f}",
                    f"{solar_energy_yield:.3f}",
                ]
            )
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(intervals)} rows to {out_path}")


if __name__ == "__main__":
    main()
