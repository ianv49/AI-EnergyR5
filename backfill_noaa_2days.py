import sys
import os
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db_connector import get_connection

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = 'upMIDPMAdLpTskzddVUHEMYlxbfeMHpA'
BASE_URL = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'
STATION_ID = '482170-99999'
SOURCE = 'noaa_gsod'

def get_realistic_irrad(temp, hour):
    if hour < 6 or hour >
