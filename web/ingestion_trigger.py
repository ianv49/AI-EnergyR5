#!/usr/bin/env python3
"""
Flask backend for All-ML Dashboard
Provides API endpoints for retraining ML models and triggering data pipeline operations.
"""

from flask import Flask, request, jsonify
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Get the project root directory (parent of web/)
PROJECT_ROOT = Path(__file__).parent.parent

@app.route('/api/retrain', methods=['POST'])
def retrain():
    """
    Retrain ML model based on selected data sources.
    
    Request body:
    {
      "sources": ["nasa", "opmet", "metstat", "tomr", "wethbit"]
    }
    
    Returns:
    {
      "status": "success|error",
      "message": "...",
      "timestamp": "2026-04-06 12:34:56"
    }
    """
    try:
        data = request.get_json() or {}
        sources = data.get('sources', ['nasa', 'opmet', 'metstat', 'tomr', 'wethbit'])
        
        # Validate sources
        valid_sources = {'nasa', 'opmet', 'metstat', 'tomr', 'wethbit'}
        sources = [s for s in sources if s in valid_sources]
        
        if not sources:
            return jsonify({
                'status': 'error',
                'message': 'No valid data sources selected',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 400
        
        # Run all-ml.py
        script_path = PROJECT_ROOT / 'all-ml.py'
        
        if not script_path.exists():
            return jsonify({
                'status': 'error',
                'message': f'Script not found: {script_path}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 404
        
        # Execute the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120  # 2-minute timeout
        )
        
        # Check if all-ml.txt was created/updated
        output_file = PROJECT_ROOT / 'data' / 'all-ml.txt'
        output_exists = output_file.exists()
        output_size = output_file.stat().st_size if output_exists else 0
        
        if result.returncode == 0 and output_exists:
            return jsonify({
                'status': 'success',
                'message': f'Retraining complete. Model trained on: {", ".join(sources)}',
                'sources': sources,
                'output_file': 'data/all-ml.txt',
                'output_size': output_size,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 200
        else:
            error_msg = result.stderr if result.stderr else 'Unknown error'
            return jsonify({
                'status': 'error',
                'message': f'Retraining failed: {error_msg}',
                'sources': sources,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Retraining timed out (exceeded 120 seconds)',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 504
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500


@app.route('/api/status', methods=['GET'])
def status():
    """
    Get status of the ML pipeline.
    Returns: Latest all-ml.txt info and training status.
    """
    try:
        output_file = PROJECT_ROOT / 'data' / 'all-ml.txt'
        
        if not output_file.exists():
            return jsonify({
                'status': 'no_output',
                'message': 'No training output yet',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 200
        
        # Get file info
        stat = output_file.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'status': 'ready',
            'output_file': 'data/all-ml.txt',
            'size_bytes': stat.st_size,
            'last_updated': mod_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking status: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'All-ML Backend',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }), 200


if __name__ == '__main__':
    print("🚀 All-ML Backend API Server")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    print("🔗 Starting Flask server on http://127.0.0.1:5000")
    print("\nAvailable endpoints:")
    print("  POST   /api/retrain     - Retrain ML model")
    print("  GET    /api/status      - Get pipeline status")
    print("  GET    /health          - Health check")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
