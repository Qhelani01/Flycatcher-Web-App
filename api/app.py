from http.server import BaseHTTPRequestHandler
import json
import requests
import time
import os
from urllib.parse import urlparse, parse_qs

# Cache for eBird taxonomy data
TAXONOMY_CACHE = {}
TAXONOMY_CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # Cache for 1 hour

# eBird API configuration
EBIRD_API_KEY = os.environ.get('EBIRD_API_KEY')
EBIRD_BASE = "https://api.ebird.org/v2"
UA = "FlycatcherApp/1.0 (+https://example.local)"

class VercelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            if path == '/api/config':
                response = self.handle_config()
            elif path == '/api/observations':
                response = self.handle_observations(query_params)
            elif path.startswith('/api/species/'):
                species_code = path.split('/')[-1]
                response = self.handle_species_info(species_code)
            else:
                response = {"error": "Endpoint not found"}
                self.send_response(404)
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_config(self):
        """Return configuration for the frontend"""
        return {
            "google_maps_api_key": os.environ.get('GOOGLE_MAPS_API_KEY', ''),
            "map_default_lat": -22.9576,
            "map_default_lng": 18.4904,
            "map_default_zoom": 6
        }
    
    def handle_observations(self, query_params):
        """Handle eBird observations request"""
        if not EBIRD_API_KEY:
            return {"error": "Server missing EBIRD_API_KEY"}
        
        region = query_params.get('region', ['ZA'])[0]
        back = query_params.get('back', ['7'])[0]
        max_results = query_params.get('maxResults', ['1000'])[0]
        
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
                return {"observations": normalized}
            else:
                return {"error": f"eBird API error: {r.status_code}"}
        except requests.RequestException as e:
            return {"error": "Network error contacting eBird", "detail": str(e)}
    
    def handle_species_info(self, species_code):
        """Get detailed information about a specific bird species from eBird"""
        if not EBIRD_API_KEY:
            return {"error": "Server missing EBIRD_API_KEY"}
        
        global TAXONOMY_CACHE, TAXONOMY_CACHE_TIMESTAMP
        
        # Check if we need to refresh the cache
        current_time = time.time()
        
        if (current_time - TAXONOMY_CACHE_TIMESTAMP > CACHE_DURATION or
            not TAXONOMY_CACHE or species_code not in TAXONOMY_CACHE):
            
            # Fetch taxonomy data from eBird
            url = f"{EBIRD_BASE}/ref/taxonomy/ebird"
            headers = {
                "X-eBirdApiToken": EBIRD_API_KEY,
                "Accept": "text/csv",
                "User-Agent": UA,
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
                    return {"error": f"eBird taxonomy API error: {r.status_code}"}
                    
            except requests.RequestException as e:
                return {"error": "Network error contacting eBird", "detail": str(e)}
        
        # Look up species from cache
        if species_code in TAXONOMY_CACHE:
            species_data = TAXONOMY_CACHE[species_code]
            return {
                "species_code": species_code,
                "common_name": species_data["common_name"],
                "family": species_data["family"],
                "order": species_data["order"]
            }
        else:
            return {
                "species_code": species_code,
                "common_name": "Species not found",
                "family": "Family information not available",
                "order": "Order information not available",
                "note": f"Species code '{species_code}' was not found in eBird's taxonomy database."
            }

# Vercel serverless function handler
def handler(request, context):
    return VercelHandler().do_GET()

# For local testing
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('localhost', 8000), VercelHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
