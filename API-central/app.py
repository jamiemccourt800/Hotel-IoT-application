from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

# VictoriaMetrics settings
VICTORIA_METRICS_URL = os.getenv("VICTORIA_METRICS_URL", "http://victoria-metrics:8428")

@app.route('/health', methods=['GET'])
def health_check():
    try:
        response = requests.get(f"{VICTORIA_METRICS_URL}/health")
        return jsonify({"status": "healthy" if response.status_code == 200 else "unhealthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)})
    
@app.route('/hotels', methods=['GET'])
def list_hotels():
    """
    Get a list of hotels from Victoria Metrics based on hotel label
    """
    try:
        # Query to get all unique hotel values from the hotel label
        response = requests.get(
            f'{VICTORIA_METRICS_URL}/api/v1/label/hotel_id/values',
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Failed to query Victoria Metrics',
                'status_code': response.status_code
            }), 500
        
        data = response.json()
        
        if data.get('status') != 'success':
            return jsonify({
                'error': 'Query failed',
                'message': data.get('error', 'Unknown error')
            }), 400
        
        hotels = data.get('data', [])
        
        return jsonify({
            'hotels': hotels,
            'count': len(hotels)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to connect to Victoria Metrics',
            'message': str(e)
        }), 503
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500 

@app.route('/hotels/<hotel_name>/rooms', methods=['GET'])
def list_rooms_by_hotel(hotel_name):
    """
    Get a list of rooms for a specific hotel
    """
    try:
        # Query to get all series with the specified hotel label
        query = f'{{hotel_id="{hotel_name}"}}'
        params = {'match[]': query}
        
        response = requests.get(
            f'{VICTORIA_METRICS_URL}/api/v1/series',
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Failed to query Victoria Metrics',
                'status_code': response.status_code
            }), 500
        
        data = response.json()
        
        if data.get('status') != 'success':
            return jsonify({
                'error': 'Query failed',
                'message': data.get('error', 'Unknown error')
            }), 400
        
        series = data.get('data', [])
        
        # Extract unique room names from the series
        rooms = set()
        for serie in series:
            if 'room' in serie:
                rooms.add(serie['room'])
        
        rooms_list = sorted(list(rooms))
        
        return jsonify({
            'hotel': hotel_name,
            'rooms': rooms_list,
            'count': len(rooms_list)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to connect to Victoria Metrics',
            'message': str(e)
        }), 503
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500  
    
if __name__ == '__main__':
    port = int(os.getenv("API_PORT", 5000))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug)