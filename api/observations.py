import os
import json
import requests
from urllib.parse import parse_qs

def handler(request, context):
    """Handle eBird observations request"""
    # Get API key from environment
    ebird_api_key = os.environ.get('EBIRD_API_KEY')
    if not ebird_api_key:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Server missing EBIRD_API_KEY"})
        }
    
    # Parse query parameters
    query_string = request.get('queryStringParameters', {}) or {}
    region = query_string.get('region', 'ZA')
    back = query_string.get('back', '7')
    max_results = query_string.get('maxResults', '1000')
    
    # eBird API configuration
    ebird_base = "https://api.ebird.org/v2"
    ua = "FlycatcherApp/1.0 (+https://example.local)"
    
    url = f"{ebird_base}/data/obs/{region}/recent"
    params = {
        'back': back,
        'maxResults': max_results
    }
    headers = {
        "X-eBirdApiToken": ebird_api_key,
        "User-Agent": ua,
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            normalized = []
            for item in data:
                species_code = item.get("speciesCode")
                normalized.append({
                    "species_code": species_code,
                    "common_name": item.get("comName"),
                    "scientific_name": item.get("sciName"),
                    "observation_date": item.get("obsDt"),
                    "latitude": item.get("lat"),
                    "longitude": item.get("lng"),
                    "count": item.get("howMany"),
                    "location_name": item.get("locName"),
                })
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"observations": normalized})
            }
        else:
            return {
                'statusCode': r.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": f"eBird API error: {r.status_code}"})
            }
    except requests.RequestException as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Network error contacting eBird", "detail": str(e)})
        }
