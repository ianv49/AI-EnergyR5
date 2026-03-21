# AI-EnergyR5
AI-Driven Predictive Maintenance for Renewable Energy Assets 
# AI-Driven Predictive Maintenance for Renewable Energy Assets

This project develops a cross-platform application for predictive maintenance of renewable energy assets (wind turbines, solar panels, inverters, batteries). It uses IoT sensor data, external weather/solar APIs, and AI/ML models to forecast failures and optimize maintenance schedules.

---

## 🚀 Features
- Real-time sensor data ingestion (temperature, humidity, irradiance, wind speed).
- External API integration (Open-Meteo, NASA POWER, Tomorrow.io).
- Local PostgreSQL + TimescaleDB storage for time-series data.
- Preprocessing scripts for normalization, cleaning, and interpolation.
- Ready for deployment on Raspberry Pi 4, but fully compatible with Mac and Windows laptops during development.

---

## 🛠️ Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd AI-EnergyR5
```

#### Project Structure
```
AI-EnergyR5/
│
├── README.md             # Documentation for setup and usage
├── TODO.md               # Task tracking and project roadmap
├── config.py             # Configuration settings (API keys, database credentials)
├── requirements.txt      # List of Python dependencies
├── check_schema.py       # Schema validation script
├── temp_summary.py       # Temporary data summary script
│
├── api_wrappers/         # API wrappers (active + Skip)
│   ├── meteostat.py      # Meteostat RapidAPI (collect5.txt)
│   ├── meteostat_native.py # Meteostat lib
│   ├── nasa_power.py     # NASA (collect2.txt, 10k+)
│   ├── noaa.py           # NOAA (Skip)
│   ├── open_meteo.py     # Open-Meteo (collect3.txt)
│   ├── openweather.py    # Legacy
│   ├── pvoutput.py       # PVOutput (Skip)
│   └── solcast.py        # Solcast (collect4.txt, Skip quota)
│
├── data/                 # Data files and logs (collectN.txt = source mapping)
│   ├── collect1.txt      # sim sensor data
│   ├── collect2.txt      # nasa_power data (10k+ rows)
│   ├── collect3.txt      # open_meteo data
│   ├── collect4.txt      # solcast data (limited)
│   ├── collect5.txt      # meteostat data (6 rows)
│   ├── collectAll.txt    # All combined
│   ├── meteostat_march2026.txt # raw JSON
│   ├── sensor_data.csv   # CSV sensor data
│   └── sensor_logs.txt   # Plain text sensor logs
│
├── db/                   # Database setup and connectors
│   ├── api_ingest_openweather.py # OpenWeather API ingestion with energy calculations
│   ├── db_connector.py   # Python script for DB connection
│   ├── db_ingest.py      # Data ingestion script with logging
│   ├── fix_source_labels.py # Fix source labels in database
│   ├── schema.sql        # SQL table definitions (11 columns including energy metrics)
│   ├── sensor_stream_sim.py # Sensor stream simulation
│   └── test_connection.py # Quick connection test script
│
├── docs/                 # Documentation and notes
│   └── myNotes.txt       # Development notes and progress logs
│
├── logs/                 # Log files with daily rotation
│   ├── ingestion.log     # Today's ingestion log
│   └── ingestion.log.YYYY-MM-DD # Rotated daily logs
│
├── notebooks/            # Jupyter notebooks for demos
│   └── data_pipeline_demo.py # Step-by-step interactive demo
│
├── preprocessing/        # Data cleaning and preprocessing scripts
│   └── preprocess.py     # Normalize and clean sensor logs
│
├── scripts/              # Utility scripts
│   ├── capture_weather_data.py # Automated weather data capture
│   ├── count_data_sources.py   # Count data sources utility
│   ├── data_collector.py       # Data collection with validation
│   ├── run_ingest.bat          # Batch file for scheduled ingestion
│   └── show_recent_data.py     # Display recent sensor data
│
├── sensors/              # Sensor data scripts
│   └── sensor_logs.txt   # Sensor logs
│
├── tests/                # Testing and validation scripts
│   ├── check_schema.py   # Schema validation
│   └── test_imports.py   # Import testing
│
└── web/                  # Web-related files
    ├── dashboard.html    # HTML interface with 3 data tables (Sim, Weather, NASA)
    ├── generate_html_table.py # HTML table generation
    ├── ingestion_trigger.py   # Flask endpoint for data fetching and file generation
    ├── latest_weather_data.html # Latest weather data display
    ├── data/             # Web-specific data files
    │   └── sensor_logs.txt
    └── logs/             # Web-specific logs
        └── ingestion.log
```


### 2. PostgreSQL Database Management

This project uses PostgreSQL as the database backend. Follow these steps to set up and manage your database:

#### Prerequisites
- PostgreSQL installed (portable or standard installation)
- Python environment with `psycopg2` and `python-dotenv` installed

#### Step 1: Configure Environment Variables

Create a `.env` file in the project root with your database credentials:

```bash
# .env file
DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_db
DB_USER=postgres
DB_PASS=your_password
```

> **Note:** The `db/db_connector.py` script automatically loads these variables. Default values are provided if `.env` is not present.

#### Step 2: Start PostgreSQL Server

**Windows (Command Prompt):**
```bash
cd "D:\My Documents\tools\postgresql\pgsql\bin"
pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" -l logfile start
```

**Verify server is running:**
```bash
pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" status
```

#### Step 3: Initialize Database Schema

**Important:** All commands below must be run from your **project directory**, not from the PostgreSQL bin directory.

First, change to your project directory:
```bash
cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
```

Then run the schema script using the full path to psql.exe:
```bash
"D:\My Documents\tools\postgresql\pgsql\bin\psql.exe" -U postgres -f db/schema.sql
```

**Database Schema (11 columns):**

| Column | Type | Description |
|--------|------|-------------|
| rn | SERIAL | Auto-incrementing row number (Primary Key) |
| timestamp | TIMESTAMP | Data collection timestamp |
| temperature | DECIMAL(5,2) | Temperature in Celsius |
| humidity | DECIMAL(5,2) | Relative humidity percentage |
| wind_speed | DECIMAL(5,2) | Wind speed in m/s |
| cloudiness | DECIMAL(5,2) | Cloud cover percentage |
| uv_index | DECIMAL(5,2) | UV index value |
| irradiance | DECIMAL(7,2) | Solar irradiance in W/m² |
| wind_power_density | DECIMAL(7,2) | Wind power density in W/m² |
| solar_energy_yield | DECIMAL(7,3) | Solar energy yield in kWh/m²/day |
| source | VARCHAR(50) | Data source (sim, openweather, nasa_power) |

#### Step 4: Test Database Connection

**Important:** Run this from your project directory, not from the PostgreSQL bin directory.

Change to your project directory:
```bash
cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
```

Then run the connection test:
```bash
py db/test_connection.py
```

**Expected output:**
- ✅ Database connection confirmation
- 📊 Total row count
- Breakdown by source:
  - Sim data: X rows
  - OpenWeather data: X rows
  - NASA POWER data: X rows
- Latest row samples from each source

#### Step 5: Stop PostgreSQL Server

When finished, stop the server gracefully:

```bash
pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" stop
```

#### Quick Reference

| Task | Command |
|------|---------|
| Start server | `pg_ctl.exe -D "path\to\data" -l logfile start` |
| Stop server | `pg_ctl.exe -D "path\to\data" stop` |
| Check status | `pg_ctl.exe -D "path\to\data" status` |
| Test connection | `py db/test_connection.py` |
| View schema | `"D:\My Documents\tools\postgresql\pgsql\bin\psql.exe" -U postgres -d energy_db -c "\d sensor_data"` |

#### Troubleshooting

- **Connection failed**: Verify PostgreSQL is running and `.env` credentials are correct
- **Database does not exist**: Run `db/schema.sql` to initialize
- **Permission denied**: Check PostgreSQL user privileges
- **Port already in use**: Ensure no other PostgreSQL instance is running on port 5432
- **"psql not recognized"**: Use the full path to `psql.exe` as shown in the commands above
- **"can't open file"**: Make sure you're running Python commands from the project directory, not from PostgreSQL bin directory

> For detailed development notes, refer to `docs/myNotes.txt`

---

## 📖 User Guide (Quick Start: Open Dashboard)

#### Overview
This guide walks you through testing Phase 8's real-time data collection features and viewing the results in the web interface. Phase 8 includes two data collection methods: manual trigger and scheduled ingestion. By the end of this guide, you'll see your collected data displayed in interactive charts and tables. Choose between the Command-Line Method for step-by-step terminal instructions or the HTML Interface Method for a user-friendly button-based experience.

#### Prerequisites (What You Need First)
Before starting, make sure you have:
- PostgreSQL database running (see PostgreSQL Database Management section above)
- Python environment with all packages installed (`pip install -r requirements.txt`)
- Internet connection (needed for weather and solar data APIs)
- Your project folder open in VS Code or terminal

#### Command-Line Method

##### Step 1: Prepare Your Environment

1. **Check if PostgreSQL is running**:
   - Open Command Prompt: Press `Win + R`, type `cmd`, press Enter
   - Navigate to PostgreSQL: `cd "D:\My Documents\tools\postgresql\pgsql\bin"`
   - Check status: `pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" status`
   - If not running, start it: `pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" -l logfile start`

2. **Verify database connection**:
   - Change to your project directory: 
      `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"`
   - Run: `py db/test_connection.py`
   - You should see existing sensor data in a table format

##### Step 2: Test Manual Data Collection

Manual collection lets you trigger data ingestion instantly via a web API call.

1. **Open your first Command Prompt window** and navigate to the web folder:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"
   ```

2. **Start the web server**:
   ```bash
   py ingestion_trigger.py
   ```
   - You should see: "Running on http://0.0.0.0:5000"
   - Keep this window open - the server is now running

3. **Open a second Command Prompt window** (don't close the first one):
   - Navigate to the same web folder: `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"`

4. **Trigger data collection manually**:
   ```bash
   curl -X POST http://localhost:5000/trigger_ingestion
   ```
   click this: http://localhost:5000
   - This sends a request to collect new sensor data
   - The response will show how many data points were collected (typically 20 rows: 10 weather + 10 solar irradiance)
   - **Status**: ✅ Working - Successfully tested and integrated into HTML dashboard

5. **Check the server window** (first Command Prompt):
   - You should see messages like:
     - "Collecting weather data from OpenWeather API..."
     - "Collecting solar data from NASA POWER API..."
     - "Data collection completed. Rows added: 20"

6. **Verify data was saved to database**:
   - Change to project directory: `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"`
   - Run: `py db/test_connection.py`
   - You should see new rows added to your sensor data table
   - Look for recent timestamps in the data

**If no new data appears**, follow these troubleshooting steps:

1. **Stop the current Flask server** (Ctrl+C in the first Command Prompt window)
2. **Restart the Flask server**:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"
   py ingestion_trigger.py
   ```
3. **Run the curl command again**:
   ```bash
   curl -X POST http://localhost:5000/trigger_ingestion
   ```
4. **Check if data was saved**:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
   py db/test_connection.py
   ```


##### Step 3: Test Automatic Data Collection (Optional)

Automatic collection runs daily after 8 PM, but you can test the function directly.

1. **In a Python session or new Command Prompt**, change to project directory:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
   ```

2. **Run the test**:
   ```bash
   py -c "from web.ingestion_trigger import perform_continuous_ingestion; result = perform_continuous_ingestion(); print('Result:', result)"
   ```

3. **What you'll see**:
   - **Before 8 PM**: `{'success': True, 'message': 'Not yet 8 PM - skipping scheduled ingestion', 'total_rows': 0}`
   - **After 8 PM**: The system will collect historical data and show rows added

##### Step 4: View Your Data in the Web Interface

Now that you've collected data, let's see it in the web dashboard!

1. **Open a new Command Prompt window** and navigate to the web folder:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"
   ```

2. **Open the HTML dashboard**:
   - Open your web browser and navigate to http://localhost:5000
   - The dashboard will load and show your sensor data

3. **Explore the dashboard**:
   - **Table View**: See all your sensor data in a neat table format
     - Columns: timestamp, temperature, humidity, irradiance, wind_speed
     - Data is sorted by timestamp (newest first)
   - **Data Tables View**: Three separate tables showing different data sources
     - Sim Data: Simulated sensor readings
     - Weather Data: OpenWeather API data
     - NASA POWER Data: Solar irradiance data
   - **Status Indicators**: Real-time feedback on system operations
     - Success/error messages for each operation
     - Row counts and data source breakdowns


4. **Alternative: View HTML Table**:
   - Change to project directory: `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"`
   - Run: `py web/generate_html_table.py`
   - This creates an HTML file you can open in any browser
   - Shows the same data in a formatted table

##### Step 5: Check Logs and Verify Everything Worked

1. **View the ingestion logs**:
   - Open `logs/ingestion.log` in your project folder
   - Look for recent entries showing:
     - When data collection started
     - How many rows were added
     - Any error messages (if something went wrong)

2. **Final database check**:
   - Change to project directory: `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"`
   - Run: `py db/test_connection.py`
   - Confirm all your new data is there
   - Count should be higher than before you started

#### HTML Interface Method

For a more user-friendly experience, start directly with the interactive HTML interface that provides clickable buttons for all Phase 8 steps and routines.

##### Prerequisites
- Python environment with all packages installed (`pip install -r requirements.txt`)
- Internet connection for API data
- PostgreSQL database (will be started via HTML interface)

##### Step 1: Launch the HTML Interface

1. **Navigate to the web folder**:
   ```bash
   cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"
   ```

2. **Start the Flask web server and open HTML interface**:
   ```bash
   py ingestion_trigger.py
   ```
   - The server will start and run on `http://0.0.0.0:5000`
   - You should see: "Running on http://0.0.0.0:5000"
   - Keep this window open
   - Access the dashboard at: `http://10.243.119.221:5000` (or `http://localhost:5000` if running locally)
   - note that IP is changing on every new start of web server.
   - web server feb6: http://10.243.120.172:5000/

##### Step 2: Use the Interactive Buttons

The HTML page provides buttons for each Phase 8 routine with function descriptions:

**System Setup Buttons:**
- **Start Flask Web Server**: Launches the Flask server (already running when you open the page)
- **Check PostgreSQL Status**: Verifies if PostgreSQL database server is running
- **Verify DB Connection**: Tests database connectivity and shows existing data

**Data Collection Buttons:**
- **Trigger Data Ingestion**: Manually collects sensor data from APIs (weather + solar)
- **Test Automatic Ingestion**: Simulates scheduled data collection (time-based)

**Visualization Buttons:**
- **View HTML Dashboard**: Opens the Flask web interface with data tables
- **View HTML Table**: Generates and displays data in HTML table format


**Monitoring Buttons:**
- **View Ingestion Logs**: Shows recent log entries with timestamps and status
- **Final DB Check**: Performs final verification of data storage

##### Step 3: Monitor Routine Completion

Each button provides real-time feedback on routine completion:

- **Success Indicators**: Green alerts showing "Success!" with details like rows added, data fetched, etc.
- **Progress Messages**: Loading spinners and "Processing..." messages during execution
- **Error Handling**: Red alerts for failures with specific error messages
- **Status Updates**: Real-time updates on data collection progress, API calls, and database operations

##### Step 4: Complete the Full Phase 8 Routine

Follow this sequence for complete Phase 8 testing:

1. **Environment Setup**:
   - Click "Check PostgreSQL Status" → Should show "running"
   - Click "Verify DB Connection" → Should display existing sensor data table

2. **Data Collection**:
   - Click "Trigger Data Ingestion" → Collects 10 weather + 10 solar data points
   - Click "Test Automatic Ingestion" → Tests scheduled collection logic

3. **Data Visualization**:
   - Click "View HTML Dashboard" → Opens the web interface at http://localhost:5000
   - Click "View HTML Table" → Shows data in formatted HTML table


4. **Verification**:
   - Click "View Ingestion Logs" → Check for successful data collection entries
   - Click "Final DB Check" → Confirm new data rows were added to database

##### Step 5: Error Logs and Troubleshooting

The bottom of the HTML page includes 5 rows for error logs and troubleshooting:

1. **Real-time Error Display**: Errors appear immediately below buttons with red alerts
2. **Log Viewer**: "View Ingestion Logs" button shows detailed server logs
3. **Status Messages**: Each button shows success/failure status with details
4. **Network Issues**: API failures and connection problems are logged
5. **Database Errors**: Connection failures and query errors are displayed

#### What You Should See in the Web Interface

After following these steps, your web dashboard should show:
- **Recent sensor readings** with timestamps from when you triggered collection
- **Three data tables** organized by source (Sim, Weather, NASA POWER)
- **Real data** from OpenWeather API (weather) and NASA POWER API (solar irradiance)
- **Clean, organized display** that's easy to read and understand


#### Troubleshooting

If something doesn't work:

- **"Command not found"**: Make sure you're in the correct folder
- **"Connection failed"**: Check if PostgreSQL is running (Step 1)
- **"Import error"**: Run `pip install -r requirements.txt`
- **No data collected**: Check your internet connection and API keys in `config.py`
- **Dashboard won't open**: Make sure no other programs are using port 5000


**Common Issues and Solutions:**
- **"Flask server not responding"**: Restart `py ingestion_trigger.py`
- **"PostgreSQL not running"**: Use "Check PostgreSQL Status" button to diagnose
- **"API key errors"**: Check `config.py` for valid API keys
- **"No data collected"**: Verify internet connection and API limits
- **"Flask server won't start"**: Check if port 5000 is available


#### Quick Reference Commands

```bash
# Check PostgreSQL status
cd "D:\My Documents\tools\postgresql\pgsql\bin"
pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" status

# Start web server for data collection
cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5\web"
py ingestion_trigger.py

# Trigger manual data collection
curl -X POST http://localhost:5000/trigger_ingestion

# Open web dashboard to view data
# Navigate to http://localhost:5000 after starting the Flask server


# Check database contents (from project directory)
cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
py db/test_connection.py

# Test automatic collection (from project directory)
cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"
py -c "from web.ingestion_trigger import perform_continuous_ingestion; print(perform_continuous_ingestion())"
```

### Prerequisites
- PostgreSQL running (see Development Setup)
- `pip install -r requirements.txt`
- Internet for APIs

### 5 Steps to Dashboard:
1. **Start PostgreSQL**: `cd "D:\My Documents\tools\postgresql\pgsql\bin" && pg_ctl.exe -D "D:\My Documents\tools\postgresql\pgsql\data" start`

2. **Start Flask**: `cd "d:/My Documents/ee/1_Tester_cee/AI/AI-EnergyR5/web" && py ingestion_trigger.py` (keep open, http://localhost:5000)

3. **Trigger Data** (optional): New terminal `cd web && curl -X POST http://localhost:5000/trigger_ingestion`

4. **Open Dashboard**: `start web/dashboard.html` or browser localhost:5000 (tables for Sim/NASA/Open-Meteo/etc.)

5. **Verify**: `py db/test_connection.py`

**Logs**: logs/ingestion.log

---

## 📋 Project Phases

The project is organized into phases for systematic development. Below is the latest status of all phases with detailed sub-steps:

### Phase 1: Environment Setup ✅ Done
- Install PostgreSQL portable binaries
- Initialize database cluster (initdb)
- Start PostgreSQL manually (pg_ctl)
- Connect with psql

### Phase 2: Database Schema ✅ Done
- Create energy_db database
- Define sensor_data table schema
- Verify schema with \d sensor_data

### Phase 3: Python Integration ✅ Done
- Install psycopg2 driver
- Create db_ingest.py script
- Connect Python to PostgreSQL
- Insert test row via Python
- Fetch and display rows via Python

### Phase 4: Log Ingestion ✅ Done
- Adapt script to read sensor_logs.txt
- Insert multiple rows from file
- Verify ingestion with query output

### Phase 5: Enhancements ✅ Done
- Handle duplicate entries (unique timestamp + ON CONFLICT)
- Format timestamp output (seconds only)
- Optional: pretty table output
- Row count before/after ingestion
- Skip header line in text ingestion
- Modularize connection into db_connector.py
- Add test_connection.py script
- Show top/bottom rows in test script

### Phase 6: Next Steps ✅ Done
- Automate ingestion (batch file or cron job)
- Extend ingestion for CSV/real sensor streams
- Dashboard/visualization integration
- Add permanent log file output (logs/ingestion.log)
- Daily log rotation (TimedRotatingFileHandler)

### Phase 7: Visualization & Dashboard ✅ Done
- Generate HTML tables from database data
- Build simple Flask web interface with data tables
- Display four data sources (Sim, NASA POWER, Open-Meteo) in separate tables


### Phase 8: Real-Time Ingestion ✅ Done
- Simulate sensor streams (append rows every minute) ✅ Done
- Implement manual trigger for on-demand ingestion ✅ Done
- Enable continuous ingestion pipeline ✅ Done
- HTML interface integration for Phase 8 steps ✅ Done
- Backfill scripts for historical data (NASA POWER, Open-Meteo) ✅ Done


### Phase 9: Web-Sensor Data Integration ⏳ Partial
- Connect to Open-Meteo API for local weather data ✅ Done
- Ingest NASA POWER API for solar irradiance and climate data ✅ Done
- Open-Meteo and NASA POWER backfill scripts for historical data ✅ Done
- Integrate PVOutput API for solar PV system performance **Skip** (no free use of historical API) ⏳ Skipped
- Integrate NOAA Climate Data API **Skip** (not able to fetch API for 2025) ⏳ Skipped
- Integrate Solcast API **Skip** (student API key has very low fetch limit) ⏳ Skipped
- Integrate Meteostat API ⏳ Partial (limited historical data ingested)
- Integrate Weatherbit API ✅ Done (2025 historical data fetched + stored)
- Normalize and store web-sensor data into sensor_data table ✅ Done
- Combine local sensor + web API data for richer analytics ✅ Done

#### Available Data Sources
| Source | Description | Backfill Scripts | Status | Reason |
|--------|-------------|-----------------|--------|--------|
| sim | Simulated sensor data | N/A (generated locally) | ✅ Active | Testing & validation |
| nasa_power | NASA POWER solar irradiance data | backfill_nasa_*.py, run_nasa_ingestion.py | ✅ Active | Free API, reliable data |
| open_meteo | Open-Meteo weather data | backfill_open_meteo*.py, fetch_open_meteo*.py | ✅ Active | Free API, no key required |
| weatherbit | Weatherbit historical weather data | fetch_weatherbit_2025.py (2025 history) | ✅ Active | Full 2025 history integrated |
| meteostat | Meteostat historical weather data (temp/hum/wind) | backfill_meteostat.py, fetch_meteostat_feb2026.py, ingest_meteostat_feb2026.py | ✅ Limited | Partial 2026 data available |
| solcast | Solcast solar irradiance (GHI/DNI/DHI + wind/temp) | backfill_solcast_feb2026.py | **Skip** | Student API key quota too low |
| pvoutput | PVOutput solar PV system data | backfill_pvoutput*.py (planned) | **Skip** | No free historical data access (401 auth) |
| noaa | NOAA Climate Data | backfill_noaa*.py (planned) | **Skip** | Consistent API timeouts/502 errors |

#### API Status Details
**Active APIs:**
- **NASA POWER** ✅: Free, no authentication required. Provides comprehensive solar irradiance and meteorological data for historical periods.
- **Open-Meteo** ✅: Free API with no API key needed. Delivers hourly historical weather data including temperature, humidity, wind speed, and solar radiation.
- **Weatherbit** ✅: Successfully integrated with full 2025 historical hourly data (10,909 records).
- **Meteostat** ⏳: Limited integration with partial data for early 2026 periods.

**Skipped APIs:**
- **NOAA**: Consistent API timeouts and 502 errors. Unable to fetch 2025 historical data reliably.
- **PVOutput**: No free historical data access. API requires authentication but free tier doesn't support historical data queries (returns 401 Unauthorized).
- **Solcast**: Student API key has quota restrictions too low for full backfills. Limited to minimal requests per month.
- **OpenWeather**: Removed from pipeline due to authorization issues with One Call API 3.0 (401 Unauthorized on historical endpoints).

Here is a list of the API sources mentioned in your `README.md`, along with the data they provide that is relevant to your database schema:

### Actively Used APIs:

1.  **Open-Meteo**
    *   **Data Fetched:** This is one of your active data sources for weather data.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `humidity`
        *   `wind_speed`
        *   `cloudiness`
        *   `uv_index`
        *   `irradiance` (as Shortwave Radiation)

2.  **NASA POWER**
    *   **Data Fetched:** This is an active source for solar and meteorological data.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `humidity`
        *   `wind_speed`
        *   `irradiance` (as Direct solar irradiance)

3.  **Tomorrow.io**
    *   **Data Fetched:** Mentioned as a feature, this API provides a wide array of data.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `humidity`
        *   `wind_speed`
        *   `irradiance` (as GHI, DNI, and DHI)
        *   `cloudiness`
        *   `uv_index`

### Planned or Future APIs:

4.  **Solcast**
    *   **Data to be Fetched:** A planned API for solar irradiance forecasts.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `wind_speed`
        *   `irradiance` (as GHI, DNI, and DHI)
        *   `cloudiness`

5.  **Weatherbit**
    *   **Data to be Fetched:** A planned API for historical weather data.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `humidity`
        *   `wind_speed`
        *   `cloudiness`
        *   `uv_index`
        *   `irradiance` (Solar Radiation)
        Plan: Free Trial (21 Days)
            1,500 req/day
            1,500 historical req/day
            Current weather + alerts
            25 years historical
            Daily forecasts
            Hourly forecasts
            60 minute forecasts
            + Energy / Air Quality / Agweather / Climate Normals API
            Non-Commercial use only
            95.0% Uptime
            Price: $0/mo

6.  **PVOutput**
    *   **Data to be Fetched:** A planned API for community-sourced PV system performance.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `wind_speed`
        *   `irradiance` (Solar Radiation)

7.  **NOAA Climate Data**
    *   **Data to be Fetched:** A planned API for climate data from the National Oceanic and Atmospheric Administration.
    *   **Database Column Mapping:**
        *   `temperature` (Max and Min)
        *   `wind_speed` (in some datasets)
        *   `precipitation` (not a direct column in your DB, but related to cloudiness/humidity)

8.  **Meteostat**
    *   **Data to be Fetched:** A planned API for historical weather data.
    *   **Database Column Mapping:**
        *   `temperature`
        *   `humidity`
        *   `wind_speed`
        *   `sunshine duration` (related to irradiance)

#### Database Table Model
The `sensor_data` table stores web sensor data with the following 11 headers:

| Header Label | Data Type | Description | Source API |
|--------------|-----------|-------------|------------|
| Row Number | SERIAL | Auto-incrementing row identifier | Database |
| Timestamp | TIMESTAMP | Date and time of data collection | System/API |
| Temperature (°C) | DECIMAL(5,2) | Air temperature in Celsius | Open-Meteo |
| Humidity (%) | DECIMAL(5,2) | Relative humidity percentage | Open-Meteo |
| Wind Speed (m/s) | DECIMAL(5,2) | Wind speed in meters per second | Open-Meteo |
| Cloudiness (%) | DECIMAL(5,2) | Cloud cover percentage | Open-Meteo |
| UV Index | DECIMAL(3,1) | Ultraviolet index value | Open-Meteo |
| Irradiance (W/m²) | DECIMAL(7,2) | Solar irradiance in watts per square meter | NASA POWER |
| Wind Power Density (W/m²) | DECIMAL(7,2) | Wind power density | Calculated |
| Solar Energy Yield (kWh/m²/day) | DECIMAL(7,3) | Solar energy yield | Calculated |
| Source | VARCHAR(50) | Data source identifier (open_meteo/nasa_power) | System |

### Phase 10: Predictive Analytics ⏳ Pending
- Calculate averages/min/max/moving averages
- Train ML model for forecasting (scikit-learn)
- **ML Options for Forecasting (10 Options):**
  - **[1] Linear Regression with Lag Features:** Create lag features (e.g., t-1, t-24 hours) + time features (hour, day). Use LinearRegression for interpretable predictions.
  - **[2] Random Forest Regressor:** Handles non-linear patterns; robust to outliers with built-in feature importance.
  - **[3] Gradient Boosting (XGBoost):** High accuracy for tabular data; requires hyperparameter tuning.
  - **[4] Time-Series Models (ARIMA/SARIMA):** Use statsmodels for univariate forecasting with seasonality.
  - **[5] Prophet:** Facebook's library for seasonal decomposition and easy forecasting.
  - **[6] Neural Networks (MLPRegressor/TensorFlow):** For complex patterns; scalable but requires more data/tuning.
  - **[7] Support Vector Regression (SVR):** Effective for non-linear regression with kernel tricks; good for small datasets.
  - **[8] K-Nearest Neighbors (KNN) Regressor:** Simple instance-based learning; useful for local patterns in time-series.
  - **[9] AdaBoost Regressor:** Boosting ensemble method; improves weak learners iteratively.
  - **[10] Gaussian Process Regression:** Probabilistic model for uncertainty quantification in predictions.
- **Recommended Start:** Linear Regression as a baseline, evaluated with MAE/RMSE on held-out test data.
- **Cost Note:** All listed ML libraries are open-source and free to use, even for students (e.g., scikit-learn, statsmodels, Prophet, TensorFlow).

### Phase 11: Deployment & Scaling ⏳ Pending
- **Containerize the Application:** Use Docker to package the Flask web application, ingestion scripts, and all dependencies into a portable container.
- **Migrate to a Cloud Database:**
    - **Choose a Cloud Provider:** Select a managed PostgreSQL service (e.g., Amazon RDS, Azure Database for PostgreSQL, Google Cloud SQL, or Supabase).
    - **Use Supabase (Optional):** Supabase provides a hosted PostgreSQL database with a web UI and REST/API access. It can be used as a drop-in replacement for the local database.
    - **Export and Import:** Export the schema and data from the local PostgreSQL database and import it into the new cloud-hosted instance.
    - **Update Configuration:** Update the `.env` file with the new database credentials (host, port, user, password, database) for the cloud instance.
- **Deploy to Cloud:** Deploy the containerized application to a cloud platform like AWS, Azure, GCP, or any container hosting service that supports Docker.
