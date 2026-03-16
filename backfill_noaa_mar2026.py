#!/usr/bin/env python3
"""Backfill NOAA GHCND daily climate data for March 2026.

Uses NOAA CDO API (dataset=GHCND) and station ID configured via env var
`NOAA_STATION_ID` (defaults to Manila SANGLEY POINT: GHCND:RPW00041224).

The script fetches TAVG (daily avg temp), AWND (avg wind), and RHAVG (avg humidity)
for March 2026, converts them to human units, and inserts them into sensor_data.
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from db.db_connector import get_connection
from db.db_ingest import insert_sensor_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# NOAA config
NOAA_TOKEN = os.getenv('NOAA_TOKEN')
if not NOAA_TOKEN:
    raise SystemExit('NOAA_TOKEN is required in environment (.env)')

# Use station near Manila with latest data
NOAA_STATION_ID = os.getenv('NOAA_STATION_ID', 'GHCND:RPW00041224')
NOAA_DATASET = os.getenv('NOAA_DATASET', 'GHCND')

BASE_URL = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'

# March 2026 range (inclusive)
START_DATE = datetime(2026, 3, 1).date()
END_DATE = datetime(2026, 3, 31).date()

# NOAA API pagination settings
LIMIT = 1000


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


def fetch_noaa_daily(start_date, end_date):
    """Fetch daily NOAA data for the date range (inclusive).

    NOAA can be slow for large ranges; split into 7-day chunks and retry on timeouts.
    """
    results = []

    # NOAA can be unreliable; fetch one day at a time and retry briefly
    session = requests.Session()
    current_day = start_date

    while current_day <= end_date:
        logger.info(f"Fetching NOAA data for {current_day}")

        success = False
        attempts = 0

        while not success and attempts < 2:
            attempts += 1
            try:
                params = {
                    'datasetid': NOAA_DATASET,
                    'stationid': NOAA_STATION_ID,
                    'startdate': current_day.isoformat(),
                    'enddate': current_day.isoformat(),
                    'datatypeid': 'TAVG,AWND,RHAVG',
                    'limit': LIMIT,
                    'units': 'metric'
                }
                headers = {
                    'token': NOAA_TOKEN,
                    'User-Agent': 'AI-EnergyR5/1.0'
                }

                # Use a short timeout to avoid long hangs if NOAA is down
                r = session.get(BASE_URL, params=params, headers=headers, timeout=(5, 10))

                if r.status_code in (429, 500, 502, 503, 504):
                    raise requests.exceptions.HTTPError(
                        f"{r.status_code} {r.reason}", response=r
                    )

                r.raise_for_status()
                data = r.json()
                page_results = data.get('results', [])
                results.extend(page_results)
                success = True

            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                logger.warning(f"Timeout fetching NOAA data for {current_day} (attempt {attempts}): {e}")
            except requests.exceptions.HTTPError as e:
                status = getattr(e.response, 'status_code', None)
                if status in (429, 500, 502, 503, 504):
                    logger.warning(f"NOAA transient error for {current_day} (attempt {attempts}): {status}")
                else:
                    logger.error(f"HTTP error fetching NOAA data for {current_day}: {e}")
                    break
            except Exception as e:
                logger.error(f"Failed to fetch NOAA data for {current_day}: {e}")
                break

            if not success:
                from time import sleep
                delay = 5 * attempts
                logger.info(f"Retrying {current_day} in {delay}s...")
                sleep(delay)

        if not success:
            logger.warning(f"Skipping {current_day} due to repeated failures")

        current_day += timedelta(days=1)

    session.close()

    return results

        current_start = current_end + timedelta(days=1)

    return results


def normalize_daily_records(records):
    """Convert NOAA daily records into one record per day with desired fields."""
    by_date = {}

    for rec in records:
        date_str = rec.get('date')
        if not date_str:
            continue

        date = date_str.split('T')[0]
        by_date.setdefault(date, {})
        dt = by_date[date]

        dtype = rec.get('datatype')
        value = rec.get('value')

        # NOAA GHCND values are typically scaled by 10 (e.g., 277 => 27.7°C)
        if dtype in ('TAVG', 'AWND', 'RHAVG'):
            dt[dtype] = to_float_or_none(value, scale=10.0)
        else:
            dt[dtype] = to_float_or_none(value)

    # Convert to list of daily dicts
    normalized = []
    for date, vals in sorted(by_date.items()):
        # Use noon timestamp for daily record
        ts = f"{date} 12:00:00"
        temp = vals.get('TAVG')
        wind = vals.get('AWND')
        hum = vals.get('RHAVG')

        normalized.append({
            'timestamp': ts,
            'temperature': temp,
            'humidity': hum,
            'wind_speed': wind
        })

    return normalized


def insert_noaa_march_2026():
    logger.info('Starting NOAA backfill for March 2026')
    records = fetch_noaa_daily(START_DATE, END_DATE)
    if not records:
        logger.warning('No records returned from NOAA API for March 2026')
        return

    normalized = normalize_daily_records(records)
    logger.info(f'Normalized {len(normalized)} daily records for March 2026')

    conn = get_connection()
    inserted = 0

    for rec in normalized:
        ts = rec['timestamp']
        temp = rec.get('temperature')
        hum = rec.get('humidity')
        wind = rec.get('wind_speed')

        wind_power = calculate_wind_power_density(wind) if wind is not None else 0.0

        insert_sensor_data(
            conn,
            ts,
            temp,
            hum,
            0.0,  # irradiance not available from NOAA
            wind,
            source='noaa',
            wind_power_density=wind_power,
            solar_energy_yield=0.0
        )
        inserted += 1

    conn.close()
    logger.info(f'Inserted {inserted} NOAA daily records for March 2026')


if __name__ == '__main__':
    insert_noaa_march_2026()
