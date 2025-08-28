from flask import Flask, jsonify, request, send_from_directory
import requests
from datetime import datetime
import time

# Load API keys
try:
    from api_keys import EBIRD_API_KEY, DEFAULT_REGION, GOOGLE_MAPS_API_KEY
except Exception:
    EBIRD_API_KEY = None
    DEFAULT_REGION = "ZA"
    GOOGLE_MAPS_API_KEY = ""

# Cache for eBird taxonomy data
TAXONOMY_CACHE = {}
TAXONOMY_CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # Cache for 1 hour

app = Flask(__name__)

# Serve frontend files
@app.route('/')
def landing():
    return send_from_directory('frontend', 'landing.html')

@app.route('/app')
def app_page():
    return send_from_directory('frontend', 'app.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

# API configuration endpoint
@app.route('/api/config')
def config():
    return jsonify({
        "google_maps_api_key": GOOGLE_MAPS_API_KEY,
        "map_default_lat": -22.9576,
        "map_default_lng": 18.4904,
        "map_default_zoom": 6
    })

# ---- eBird proxy ----
EBIRD_BASE = "https://api.ebird.org/v2"
UA = "FlycatcherApp/1.0 (+https://example.local)"

@app.route("/api/observations")
def observations():
    """Proxy eBird observations API"""
    if not EBIRD_API_KEY:
        return jsonify({"error": "Server missing EBIRD_API_KEY"}), 500
    
    region = request.args.get('region', DEFAULT_REGION)
    back = request.args.get('back', '7')
    max_results = request.args.get('maxResults', '1000')
    
    url = f"{EBIRD_BASE}/data/obs/{region}/recent"
    params = {
        'back': back,
        'maxResults': max_results
    }
    headers = {
        "X-eBirdApiToken": EBIRD_API_KEY,
        "User-Agent": UA,
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            normalized = []
            for item in data:
                species_code = item.get("speciesCode")
                print(f"DEBUG: Processing species: {item.get('comName')} with code: {species_code}")
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
            return jsonify({"observations": normalized})
        else:
            return jsonify({"error": f"eBird API error: {r.status_code}"}), 502
    except requests.RequestException as e:
        return jsonify({"error": "Network error contacting eBird", "detail": str(e)}), 502

@app.route("/api/species/<species_code>")
def species_info(species_code):
    """Get detailed information about a specific bird species from eBird"""
    if not EBIRD_API_KEY:
        return jsonify({"error": "Server missing EBIRD_API_KEY"}), 500

    global TAXONOMY_CACHE, TAXONOMY_CACHE_TIMESTAMP

    # Check if we need to refresh the cache
    current_time = time.time()

    if (current_time - TAXONOMY_CACHE_TIMESTAMP > CACHE_DURATION or
        not TAXONOMY_CACHE or species_code not in TAXONOMY_CACHE):

        print(f"DEBUG: Refreshing taxonomy cache for species: {species_code}")

        # Fetch taxonomy data from eBird
        url = f"{EBIRD_BASE}/ref/taxonomy/ebird"
        headers = {
            "X-eBirdApiToken": EBIRD_API_KEY,
            "Accept": "text/csv",
            "User-Agent": UA,
        }

        try:
            r = requests.get(url, headers=headers, timeout=20)
            print(f"DEBUG: eBird taxonomy response status: {r.status_code}")

            if r.status_code == 200:
                # Parse CSV data and build cache
                csv_data = r.text
                lines = csv_data.strip().split('\n')

                # Skip header line and build cache
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 10: # Ensure enough parts for order and family
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
                print(f"DEBUG: Cached {len(TAXONOMY_CACHE)} species")
            else:
                return jsonify({"error": f"eBird taxonomy API error: {r.status_code}"}), 502

        except requests.RequestException as e:
            return jsonify({"error": "Network error contacting eBird", "detail": str(e)}), 502

    # Look up species from cache
    if species_code in TAXONOMY_CACHE:
        species_data = TAXONOMY_CACHE[species_code]
        return jsonify({
            "species_code": species_code,
            "common_name": species_data["common_name"],
            "family": species_data["family"],
            "order": species_data["order"]
        })
    else:
        return jsonify({
            "species_code": species_code,
            "common_name": "Species not found",
            "family": "Family information not available",
            "order": "Order information not available",
            "note": f"Species code '{species_code}' was not found in eBird's taxonomy database."
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
