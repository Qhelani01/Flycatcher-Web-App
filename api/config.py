import os
import json

def handler(request, context):
    """Return configuration for the frontend"""
    response = {
        "google_maps_api_key": os.environ.get('GOOGLE_MAPS_API_KEY', ''),
        "map_default_lat": -22.9576,
        "map_default_lng": 18.4904,
        "map_default_zoom": 6
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(response)
    }
