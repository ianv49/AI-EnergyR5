import requests

token = 'upMIDPMAdLpTskzddVUHEMYlxbfeMHpA'

headers = {'token': token}

params = {
    'datasetid': 'GSOD',
    'stationid': '482170-99999',
    'startdate': '2024-01-01',
    'enddate': '2024-01-03',
    'limit': 10,
    'datatypeid': 'TAVG'
}

r = requests.get('https://www.ncdc.noaa.gov/cdo-web/api/v2/data', params=params, headers=headers)

print('Status:', r.status_code)
print('URL:', r.url)
if r.status_code != 200:
    print('Error:', r.text[:500])
else:
    results = r.json().get('results', [])
    print('Success:', len(results), 'records')
    if results:
        print('Sample:', results[0])

