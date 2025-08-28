import os
import json
import requests
import time

# Cache for eBird taxonomy data
TAXONOMY_CACHE = {}
TAXONOMY_CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # Cache for 1 hour

def handler(request, context):
    """Get detailed information about a specific bird species from eBird"""
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
    
    # Get species code from path
    path = request.get('path', '')
    species_code = path.split('/')[-1] if path else ''
    
    if not species_code:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Species code required"})
        }
    
    global TAXONOMY_CACHE, TAXONOMY_CACHE_TIMESTAMP
    
    # Check if we need to refresh the cache
    current_time = time.time()
    
    if (current_time - TAXONOMY_CACHE_TIMESTAMP > CACHE_DURATION or
        not TAXONOMY_CACHE or species_code not in TAXONOMY_CACHE):
        
        # Fetch taxonomy data from eBird
        ebird_base = "https://api.ebird.org/v2"
        ua = "FlycatcherApp/1.0 (+https://example.local)"
        
        url = f"{ebird_base}/ref/taxonomy/ebird"
        headers = {
            "X-eBirdApiToken": ebird_api_key,
            "Accept": "text/csv",
            "User-Agent": ua,
        }
        
        try:
            r = requests.get(url, headers=headers, timeout=20)
            
            if r.status_code == 200:
                # Parse CSV data and build cache
                csv_data = r.text
                lines = csv_data.strip().split('\n')
                
                # Skip header line and build cache
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 10:
                            code = parts[2].strip('"')
                            com_name = parts[1].strip('"')
                            order = parts[8].strip('"')
                            family = parts[9].strip('"')
                            
                            TAXONOMY_CACHE[code] = {
                                "common_name": com_name,
                                "order": order,
                                "family": family
                            }
                
                TAXONOMY_CACHE_TIMESTAMP = current_time
            else:
                return {
                    'statusCode': r.status_code,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({"error": f"eBird taxonomy API error: {r.status_code}"})
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
    
    # Look up species from cache
    if species_code in TAXONOMY_CACHE:
        species_data = TAXONOMY_CACHE[species_code]
        response = {
            "species_code": species_code,
            "common_name": species_data["common_name"],
            "family": species_data["family"],
            "order": species_data["order"]
        }
    else:
        response = {
            "species_code": species_code,
            "common_name": "Species not found",
            "family": "Family information not available",
            "order": "Order information not available",
            "note": f"Species code '{species_code}' was not found in eBird's taxonomy database."
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }
