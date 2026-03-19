import logging
import os
import csv
from datetime import datetime
from tabulate import tabulate
from logging.handlers import TimedRotatingFileHandler
from db.db_connector import get_connection   # Import connection function

# ----------------------------
# Logging Setup (console + daily rotating file)
# ----------------------------
os.makedirs("logs", exist_ok=True)

# Console handler
console_handler = logging.StreamHandler()

# Daily rotating file handler (new file every midnight)
file_handler = TimedRotatingFileHandler(
    "logs/ingestion.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
# backupCount=7 keeps the last 7 days of logs, older ones are deleted automatically

# Formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Logger object
logger = logging.getLogger("ingestion_logger")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# ----------------------------
# Helper Functions
# ----------------------------

def count_rows(conn):
    """Return the number of rows in sensor_data table."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sensor_data;")
            result = cur.fetchone()
            return result[0]
    except Exception as e:
        logger.error(f"Error counting rows: {e}")
        return None

def insert_sensor_data(conn, timestamp, temperature, humidity, irradiance, wind_speed, source="unknown", wind_power_density=None, solar_energy_yield=None):
    """Insert one row into sensor_data table, strip microseconds, skip duplicates."""
    try:
        ts = datetime.fromisoformat(timestamp).replace(microsecond=0)
        with conn.cursor() as cur:
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
                (ts, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield)
            )
        conn.commit()
    except Exception as e:
        # Roll back the current transaction so subsequent inserts can proceed.
        try:
            conn.rollback()
        except Exception:
            pass
        logger.error(f"Insert failed: {e}")


def ingest_text_file(conn, filepath="data/sensor_logs.txt", source="sim"):
    """Read plain text log file and insert rows."""
    try:
        with open(filepath, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                # Skip header line
                if parts[0].lower() == "timestamp":
                    continue
                if len(parts) == 5:
                    timestamp, temperature, humidity, irradiance, wind_speed = parts
                    insert_sensor_data(conn, timestamp, float(temperature), float(humidity), float(irradiance), float(wind_speed), source)
        logger.info("Text file ingestion complete.")
    except FileNotFoundError:
        logger.warning(f"{filepath} not found.")
    except Exception as e:
        logger.error(f"Error ingesting text file: {e}")

def ingest_csv_file(conn, filepath="data/sensor_data.csv", source="csv"):
    """Read CSV file and insert rows."""
    try:
        with open(filepath, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                insert_sensor_data(
                    conn,
                    row["timestamp"],
                    float(row["temperature"]),
                    float(row["humidity"]),
                    float(row["irradiance"]),
                    float(row["wind_speed"]),
                    source
                )
        logger.info("CSV ingestion complete.")
    except FileNotFoundError:
        logger.warning(f"{filepath} not found.")
    except Exception as e:
        logger.error(f"Error ingesting CSV file: {e}")

def fetch_and_display(conn, limit=10):
    """Display latest rows in a pretty table."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT %s;", (limit,))
            rows = cur.fetchall()
            headers = [desc[0] for desc in cur.description]
            print(tabulate(rows, headers=headers, tablefmt="psql"))
    except Exception as e:
        logger.error(f"Error fetching rows: {e}")

def run_ingestion():
    """Run the complete ingestion process and return results."""
    conn = get_connection()

    # Count rows before ingestion
    before_count = count_rows(conn)
    logger.info(f"Rows before ingestion: {before_count}")

    # Run ingestion
    ingest_text_file(conn, "data/sensor_logs.txt")
    ingest_csv_file(conn, "data/sensor_data.csv")

    # Count rows after ingestion
    after_count = count_rows(conn)
    logger.info(f"Rows after ingestion: {after_count}")

    # Show how many new rows were added
    new_rows = 0
    if before_count is not None and after_count is not None:
        new_rows = after_count - before_count
        logger.info(f"New rows added: {new_rows}")

    conn.close()

    return {
        'success': True,
        'rows_before': before_count,
        'rows_after': after_count,
        'new_rows': new_rows
    }

# ----------------------------
# Main Script
# ----------------------------
if __name__ == "__main__":
    conn = get_connection()

    # Count rows before ingestion
    before_count = count_rows(conn)
    logger.info(f"Rows before ingestion: {before_count}")

    # Run ingestion
    ingest_text_file(conn, "data/sensor_logs.txt")
    ingest_csv_file(conn, "data/sensor_data.csv")

    # Count rows after ingestion
    after_count = count_rows(conn)
    logger.info(f"Rows after ingestion: {after_count}")

    # Show how many new rows were added
    if before_count is not None and after_count is not None:
        logger.info(f"New rows added: {after_count - before_count}")

    # Display latest rows
    fetch_and_display(conn, limit=10)

    conn.close()
