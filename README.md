# AI-EnergyR5
AI-Driven Predictive Maintenance for Renewable Energy Assets 
# AI-Driven Predictive Maintenance for Renewable Energy Assets

This project develops a cross-platform application for predictive maintenance of renewable energy assets (wind turbines, solar panels, inverters, batteries). It uses IoT sensor data, external weather/solar APIs, and AI/ML models to forecast failures and optimize maintenance schedules.

---

## 🚀 Features
- Real-time sensor data ingestion (temperature, humidity, irradiance, wind speed).
- External API integration (OpenWeather, NASA POWER, Tomorrow.io).
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
├── api_wrappers/         # External API integration modules
│   ├── nasa_power.py     # NASA POWER API wrapper for solar irradiance data
│   └── openweather.py    # OpenWeather API wrapper with wind/solar calculations
│
├── data/                 # Data files and logs
│   ├── collect1.txt      # Simulated sensor data (with wind_power_density, solar_energy_yield)
│   ├── collect2.txt      # OpenWeather API data (with wind_power_density, solar_energy_yield)
│   ├── collect3.txt      # NASA POWER data (with wind_power_density, solar_energy_yield)
│   ├── collectAll.txt    # All collected data combined
│   ├── sensor_data.csv   # CSV file for sensor data
│   └── sensor_logs.txt   # Plain text sensor log file
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

## 📖 User Guide



### Complete Step-by-Step Guide: Test Phase 8 Real-Time Data Collection and View Results in Web Interface

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
   - Change to your project directory: `cd "d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5"`
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

This complete guide takes you from setting up the environment to collecting data and viewing beautiful charts in your web browser. The Phase 8 system automatically combines simulated sensor data with real weather and solar data, giving you a comprehensive view of your renewable energy system's performance!

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
- Display three data sources (Sim, Weather, NASA) in separate tables


### Phase 8: Real-Time Ingestion 🔄 Partial
- Simulate sensor streams (append rows every minute) ✅ Done
- Implement manual trigger for on-demand ingestion ✅ Done
- Enable continuous ingestion pipeline ⏳ Pending
- HTML interface integration for Phase 8 steps ✅ Done


### Phase 9: Web-Sensor Data Integration 🔄 Partial
- Connect to OpenWeather API for local weather data ✅ Done
- Ingest NASA POWER API for solar irradiance and climate data ✅ Done
- Integrate PVOutput API for solar PV system performance ⏳ Pending
- Optional: Add other APIs (NOAA, Meteostat, etc.) ⏳ Pending
- Normalize and store web-sensor data into sensor_data table ✅ Done
- Combine local sensor + web API data for richer analytics ⏳ Pending

#### Database Table Model
The `sensor_data` table stores web sensor data with the following 11 headers:

| Header Label | Data Type | Description | Source API |
|--------------|-----------|-------------|------------|
| Row Number | SERIAL | Auto-incrementing row identifier | Database |
| Timestamp | TIMESTAMP | Date and time of data collection | System/API |
| Temperature (°C) | DECIMAL(5,2) | Air temperature in Celsius | OpenWeather |
| Humidity (%) | DECIMAL(5,2) | Relative humidity percentage | OpenWeather |
| Wind Speed (m/s) | DECIMAL(5,2) | Wind speed in meters per second | OpenWeather |
| Cloudiness (%) | DECIMAL(5,2) | Cloud cover percentage | OpenWeather |
| UV Index | DECIMAL(3,1) | Ultraviolet index value | OpenWeather |
| Irradiance (W/m²) | DECIMAL(7,2) | Solar irradiance in watts per square meter | NASA POWER |
| Wind Power Density (W/m²) | DECIMAL(7,2) | Wind power density | Calculated |
| Solar Energy Yield (kWh/m²/day) | DECIMAL(7,3) | Solar energy yield | Calculated |
| Source | VARCHAR(50) | Data source identifier (openweather/nasa_power) | System |

### Phase 10: Predictive Analytics ⏳ Pending
- Calculate averages/min/max/moving averages
- Train ML model for forecasting (scikit-learn)

### Phase 11: Deployment & Scaling ⏳ Pending
- Containerize with Docker
- Deploy to cloud (AWS/Azure/GCP)
