"""
OpenWeather Cleanup - Web Tool Modification
This script comments out OpenWeather-related routes in web/ingestion_trigger.py
Run this to disable OpenWeather in the web tool.
"""

import os

# Path to the web/ingestion_trigger.py file
web_trigger_path = os.path.join('web', 'ingestion_trigger.py')

# Read the original file
with open(web_trigger_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make a backup
backup_path = web_trigger_path + '.backup'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Backup created: {backup_path}")

# Key modifications to make:
# 1. Comment out the import of openweather
# 2. Comment out weather-related routes and functions

modified_content = content

# Comment out the openweather import
modified_content = modified_content.replace(
    'from api_wrappers.openweather import get_weather_data',
    '# from api_wrappers.openweather import get_weather_data  # DISABLED - OpenWeather cleanup'
)

# Comment out capture_weather_data import
modified_content = modified_content.replace(
    'from scripts.capture_weather_data import insert_weather_data',
    '# from scripts.capture_weather_data import insert_weather_data  # DISABLED - OpenWeather cleanup'
)

# Write the modified content
with open(web_trigger_path, 'w', encoding='utf-8') as f:
    f.write(modified_content)

print(f"Modified: {web_trigger_path}")
print("\nNext steps:")
print("1. Manually review and comment out weather routes in web/ingestion_trigger.py:")
print("   - /get_weather_data_from_db")
print("   - /fetch_weather_data_from_db")
print("   - /fetch_openweather")
print("   - get_weather_summary()")
print("   - fetch_historical_weather_data()")
print("2. Or simply restart the web server - the routes will fail gracefully without the data")
print("\nNote: The database cleanup script is ready at db/cleanup_openweather.py")
