import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('NOAA_TOKEN')
if not token:
    raise SystemExit('NOAA_TOKEN not set')

# Manila coordinates (same as Open-Meteo code)
lat, lon = 14.5995, 120.9842
# bounding box ~ 0.3 degrees (~30km) around Manila
delta = 0.3
extent = f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}"

url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations'
params = {
    'datasetid': 'GHCND',
    'extent': extent,
    'limit': 100,
    'sortfield': 'maxdate',
    'sortorder': 'desc'
}
headers = {'token': token}

r = requests.get(url, params=params, headers=headers, timeout=30)
print('Stations query status', r.status_code)
if r.status_code != 200:
    print(r.text)
    raise SystemExit(1)

stations = r.json().get('results', [])
print(f'Found {len(stations)} stations (GHCND) in bounding box {extent}')
for s in stations[:10]:
    print(f"{s.get('id')} | {s.get('name')} | mindate={s.get('mindate')} maxdate={s.get('maxdate')}")

if stations:
    best = stations[0]
    print('\nRecommended station (most recent maxdate):', best.get('id'), best.get('name'))
    print('Maxdate:', best.get('maxdate'))
