import requests
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

token = os.getenv('NOAA_TOKEN', 'upMIDPMAdLpTskzddVUHEMYlxbfeMHpA')
headers = {'token': token}

print('=== NOAA GSOD Stations near Manila ===')
extent = '14.50,120.90,14.70,121.10'  # Manila bounding box
url_stations = f'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?datasetid=GSOD&extent={extent}&stationstatus=ACTIVE&limit=20&sortfield=maxdate&sortorder=desc'
r = requests.get(url_stations, headers=headers)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    stations = data.get('results', [])
    print(f'Found {len(stations)} ACTIVE GSOD stations')
    for i, s in enumerate(stations[:10], 1):
        print(f"{i}. stationid={s.get('id', 'N/A')}, name={s.get('name', 'N/A')}, mindate={s.get('mindate', 'N/A')}, maxdate={s.get('maxdate', 'N/A')} ")
    if stations:
        best_id = stations[0]['id']
        print(f'\nRECOMMENDED: stationid={best_id}')
        
        # Test data fetch recent
        print('\n=== Test data for recent 30 days ===')
        today = date.today().strftime('%Y-%m-%d')
        month_ago = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        url_data = f'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GSOD&stationid={best_id}&startDate={month_ago}&endDate={today}&limit=100&datatypeid=TAVG,TMIN,TMAX,RHAVG,AWND,PRCP'
        r_data = requests.get(url_data, headers=headers)
        print(f'Data status: {r_data.status_code}')
        if r_data.status_code == 200:
            data_res = r_data.json()
            results = data_res.get('results', [])
            print(f'Found {len(results)} daily records')
            temps = [r for r in results if r['datatype']=='TAVG']
            if temps:
                latest = temps[0]
                print(f"Latest TAVG {latest['date']}: value={latest['value']/10} C (raw/10)")
            print('Sample datatypes:', [r['datatype'] for r in results[:5]])
        else:
            print(r_data.text[:500])
else:
    print(r.text[:1000])
