from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for
import requests
from datetime import datetime
import time
import secrets
from users import authenticate_user, get_user_by_email

# Load API keys from environment variables
import os
EBIRD_API_KEY = os.environ.get('EBIRD_API_KEY')
DEFAULT_REGION = os.environ.get('DEFAULT_REGION', 'ZA')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Cache for eBird taxonomy data
TAXONOMY_CACHE = {}
TAXONOMY_CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # Cache for 1 hour

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

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

# Authentication routes
@app.route("/api/login", methods=["POST"])
def login():
    """Handle user login"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400
    
    result = authenticate_user(email, password)
    if result["success"]:
        session['user'] = result["user"]
        return jsonify(result)
    else:
        return jsonify(result), 401

@app.route("/api/logout")
def logout():
    """Handle user logout"""
    session.pop('user', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/api/user")
def get_current_user():
    """Get current logged-in user"""
    if 'user' in session:
        return jsonify({"success": True, "user": session['user']})
    return jsonify({"success": False, "user": None})

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

@app.route("/api/geocode")
def geocode_address():
    """Geocode an address using Google Maps API"""
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Server missing GOOGLE_MAPS_API_KEY"}), 500
    
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Address parameter required"}), 400
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]
            location = result['geometry']['location']
            return jsonify({
                "success": True,
                "location": {
                    "lat": location['lat'],
                                                   "lng": location['lng']
                },
                "formatted_address": result['formatted_address']
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Geocoding failed: {data.get('status', 'Unknown error')}"
            })
            
    except requests.RequestException as e:
        return jsonify({"error": "Network error contacting Google Maps", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
