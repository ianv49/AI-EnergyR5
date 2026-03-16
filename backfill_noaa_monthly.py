#!/usr/bin/env python3
"""Backfill NOAA daily data (1 record per month) for Jan 2025 - Mar 2026.

This script fetches ONE daily record per month (using the 15th of each month) from the
NOAA CDO API (GHCND dataset). It writes failures and timeouts to logs/ingestion.log
using the existing ingestion logger.

Requirements:
- NOAA_TOKEN must be set (in .env).  This script uses the same NOAA station as the
  existing wrapper (`NOAA_STATION_ID` env var, defaulting to `GHCND:RPW00041224`).
- It will insert data into the `sensor_data` table with source='noaa'.
- It does not wait longer than 5 seconds per request; timeouts are logged and skipped.
"""

import os
from datetime import date, datetime

import psycopg2
import requests
from dotenv import load_dotenv

from db.db_ingest import insert_sensor_data, logger

# NOAA config
NOAA_TOKEN = os.getenv('NOAA_TOKEN')
if not NOAA_TOKEN:
    raise SystemExit('NOAA_TOKEN must be set in environment (.env)')

NOAA_STATION_ID = os.getenv('NOAA_STATION_ID', 'GHCND:RPW00041224')
NOAA_DATASET = os.getenv('NOAA_DATASET', 'GHCND')
BASE_URL = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'

# Date range: Jan 2025 -> Mar 2026
START_MONTH = date(2025, 1, 1)
END_MONTH = date(2026, 3, 1)

# Fetch timeout (connect, read)
TIMEOUT = (5, 5)  # seconds


def to_float_or_none(val, scale=1.0):
    if val is None:
        return None
    try:
        return float(val) / scale
    except Exception:
        return None


def calculate_wind_power_density(wind_speed_m_s):
    if wind_speed_m_s is None or wind_speed_m_s <= 0:
        return 0.0
    rho = 1.225  # kg/m3
    return round(0.5 * rho * (wind_speed_m_s ** 3), 2)


def fetch_noaa_for_date(target_date: date):
    """Fetch NOAA daily values for a single date."""
    params = {
        'datasetid': NOAA_DATASET,
        'stationid': NOAA_STATION_ID,
        'startdate': target_date.isoformat(),
        'enddate': target_date.isoformat(),
        'datatypeid': 'TAVG,AWND,RHAVG',
        'limit': 100,
        'units': 'metric',
    }
    headers = {'token': NOAA_TOKEN, 'User-Agent': 'AI-EnergyR5/1.0'}

    r = requests.get(BASE_URL, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get('results', [])


def month_date_sequence(start: date, end: date):
    """Yield the 15th of each month from start to end (inclusive)."""
    cur = date(start.year, start.month, 15)
    while cur <= end:
        yield cur
        # next month
        year = cur.year + (cur.month // 12)
        month = (cur.month % 12) + 1
        cur = date(year, month, 15)


def run_backfill():
    # Load env vars for database connection
    load_dotenv()

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "energy_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "PdM"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        logger.info("Connected to PostgreSQL successfully.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return

    inserted = 0
    skipped = 0

    for dt in month_date_sequence(START_MONTH, END_MONTH):
        try:
            logger.info(f"NOAA fetch for {dt.isoformat()} (station={NOAA_STATION_ID})")
            results = fetch_noaa_for_date(dt)

            if not results:
                logger.warning(f"NOAA returned no records for {dt.isoformat()}")
                skipped += 1
                continue

            # Pull the first TAVG/AWND/RHAVG set for that date
            # NOAA returns multiple datatype rows; we need to combine.
            data_by_type = {r['datatype']: r['value'] for r in results}
            temp = to_float_or_none(data_by_type.get('TAVG'), scale=10.0)
            wind = to_float_or_none(data_by_type.get('AWND'), scale=10.0)
            hum = to_float_or_none(data_by_type.get('RHAVG'), scale=10.0)

            # Use fixed timestamp at noon of target date
            ts = datetime(dt.year, dt.month, dt.day, 12, 0, 0).isoformat()

            wind_power = calculate_wind_power_density(wind)

            insert_sensor_data(
                conn,
                ts,
                temp,
                hum,
                0.0,  # no irradiance from NOAA
                wind,
                source='noaa',
                wind_power_density=wind_power,
                solar_energy_yield=0.0,
            )
            inserted += 1

        except requests.exceptions.Timeout as e:
            logger.error(f"NOAA timeout for {dt.isoformat()}: {e}")
            skipped += 1
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            logger.error(f"NOAA HTTP error for {dt.isoformat()}: {status} {e}")
            skipped += 1
        except Exception as e:
            logger.error(f"NOAA fetch failed for {dt.isoformat()}: {e}")
            skipped += 1

    conn.close()
    logger.info(f"NOAA backfill complete: inserted={inserted}, skipped={skipped}")


if __name__ == '__main__':
    run_backfill()
