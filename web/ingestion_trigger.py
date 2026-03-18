import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, jsonify, request
import logging
from db.db_connector import get_connection
from api_wrappers.nasa_power import get_solar_irradiance_data as get_nasa_power_data
from api_wrappers.open_meteo import get_weather_data as get_open_meteo_data
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='logs/ingestion.log', format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("web_ingestion")

@app.route('/trigger_ingestion', methods=['POST'])
def trigger_ingestion():
    try:
        logger.info("Manual ingestion triggered via web")
        
        # NASA POWER (solar irradiance)
        nasa_data = get_nasa_power_data()
        if nasa_data:
            logger.info(f"NASA POWER: {len(nasa_data)} rows")
        
        # Open-Meteo (weather)
        meteo_data = get_open_meteo_data()
        if meteo_data:
            logger.info(f"Open-Meteo: {len(meteo_data)} rows")
        
        # Meteostat (if available)
        # Note: Use backfill scripts for bulk; placeholder for real-time
        logger.info("Meteostat: Use py backfill_meteostat.py for bulk data")
        
        total_rows = (len(nasa_data) if nasa_data else 0) + (len(meteo_data) if meteo_data else 0)
        
        return jsonify({
            'success': True,
            'message': 'Ingestion complete',
            'nasa_power_rows': len(nasa_data) if nasa_data else 0,
            'open_meteo_rows': len(meteo_data) if meteo_data else 0,
            'meteostat_note': 'Run backfill_meteostat.py for data',
            'total_rows': total_rows,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import send_file

@app.route('/')
@app.route('/dashboard.html')
def dashboard():
    return send_file('dashboard.html')

@app.route('/data/collect5.txt')
def collect5_txt():
    """Serve web/data/collect5.txt - generate from project data/collect5.txt if missing."""
    project_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    project_file = os.path.join(project_data_dir, 'collect5.txt')
    
    if os.path.exists(project_file):
        return send_file(project_file)
    
    # Fallback generate to project data/
    generate_collect_txt(5, 'meteostat')
    return send_file(project_file)

@app.route('/fetch_meteostat_data_from_db')
def fetch_meteostat_db():
    """Fetch Meteostat from DB → update data/collect5.txt → jsonify."""
    try:
        logger.info('Fetch Meteostat DB → collect5.txt')
        generate_collect_txt(5, 'meteostat')
        rows = query_source_count('meteostat')
        summary = get_source_summary('meteostat')
        return jsonify({
            'success': True,
            'rows_fetched': rows,
            'summary': summary
        })
    except Exception as e:
        logger.error(f'Meteostat fetch error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_collect_txt(n, source):
    """Generic: Generate data/collectN.txt from DB source (header, [source], csv rows)."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Count
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source=%s", (source,))
    count = cur.fetchone()[0]
    
    # Summary time range
    cur.execute("""
        SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source=%s
    """, (source,))
    min_ts, max_ts = cur.fetchone()
    
    # Latest 50 rows
    cur.execute("""
        SELECT id, timestamp, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield 
        FROM sensor_data WHERE source=%s 
        ORDER BY timestamp DESC LIMIT 50
    """, (source,))
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    header = f"""# Meteostat data mirror from DB source='meteostat'
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Summary: meteostat={count} | range {min_ts} to {max_ts if max_ts else 'N/A'}

[meteostat]"""
    
    csv_rows = []
    for row in rows:
        # Handle variable cols, pad with None
        rn, ts, temp, hum, irr, wind, src, wpd, sey = row
        csv_rows.append(f"{rn or ''},{ts or ''},{temp or 0},{hum or 0},{irr or 0},{wind or 0},,,{wpd or ''},{sey or ''},{src or 'meteostat'}")
    
    content = header + '\n' + '\n'.join(csv_rows)
    
    project_collect = os.path.join(os.path.dirname(__file__), '..', '..', 'data', f'collect{n}.txt')
    with open(project_collect, 'w') as f:
        f.write(content)
    
    logger.info(f'Generated data/collect{n}.txt: {count} {source} rows')
    return content

def query_source_count(source):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source=%s", (source,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def get_source_summary(source):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT MIN(timestamp), MAX(timestamp), AVG(temperature), AVG(humidity), AVG(wind_speed), AVG(irradiance)
        FROM sensor_data WHERE source=%s
    """, (source,))
    summary = cur.fetchone()
    cur.close()
    conn.close()
    return {'min_ts': summary[0], 'max_ts': summary[1], 'avg_temp': summary[2], 'avg_hum': summary[3], 'avg_wind': summary[4], 'avg_irr': summary[5]}

if __name__ == '__main__':
    print("Running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

