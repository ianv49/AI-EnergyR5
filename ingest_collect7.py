"""Ingest Weatherbit collect7.txt data into the sensor_data database table.

This reads `data/collect7.txt` (the Weatherbit historical file in the same format as
collect1.txt) and inserts rows into sensor_data using the existing ingestion helper.

It will skip any timestamps that already exist in the table.
"""

from db.db_connector import get_connection
from db.db_ingest import count_rows, insert_sensor_data


def ingest_collect7(conn, filepath="data/collect7.txt"):
    before = count_rows(conn)
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if line.startswith("id,"):
                continue
            parts = line.split(",")
            if len(parts) < 9:
                continue
            # Fields: id,timestamp,temperature,humidity,irradiance,wind_speed,source,wind_power_density,solar_energy_yield
            _, timestamp, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield = parts[:9]
            insert_sensor_data(
                conn,
                timestamp,
                float(temperature),
                float(humidity),
                float(irradiance),
                float(wind_speed),
                source,
                float(wind_power_density),
                float(solar_energy_yield),
            )
    after = count_rows(conn)
    return before, after


if __name__ == "__main__":
    conn = get_connection()
    before, after = ingest_collect7(conn)
    print(f"Rows before: {before}")
    print(f"Rows after: {after}")
    print(f"New rows inserted: {after - before}")
    # Show some sample rows for verification
    with conn.cursor() as cur:
        cur.execute("SELECT timestamp, temperature, humidity, irradiance, wind_speed, source FROM sensor_data WHERE source = 'weatherbit' ORDER BY timestamp DESC LIMIT 5;")
        rows = cur.fetchall()
        print("\nLatest weatherbit rows:")
        for r in rows:
            print(r)
    conn.close()
