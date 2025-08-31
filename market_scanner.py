#!/usr/bin/env python3
"""market_scanner.py
Advanced Zillow market scanner for properties within specific price and size ranges.

Features:
- Configurable search radius from a center point
- Price range: $1M - $2M (configurable)
- Square footage: 1K - 2K sqft (configurable)
- Beautiful HTML output with detailed property information
- For-sale properties focus for investment opportunities

How to run:
$ pip install requests beautifulsoup4
$ python market_scanner.py --config config.json
"""

import json, statistics, requests, time, random, argparse, os, math
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Default configuration
DEFAULT_CONFIG = {
    "search_area": {
        "center": "Mission District, San Francisco, CA",
        "radius_miles": 0.5,
        "auto_bounds": True
    },
    "filters": {
        "min_price": 1000000,
        "max_price": 2000000,
        "min_sqft": 1000,
        "max_sqft": 2000,
        "include_sold": False,
        "max_sold_age_months": 6
    },
    "output": {
        "html_file": "market_scan_results.html",
        "json_file": "market_scan_data.json",
        "max_listings": 200
    }
}

class MarketScanner:
    def __init__(self, config):
        self.config = config
        self.session = self.create_session()
        self.properties = []
        self.search_bounds = self.calculate_search_bounds()
        
    def create_session(self):
        """Create configured session"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[403, 429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Origin": "https://www.zillow.com",
            "Pragma": "no-cache",
            "Referer": "https://www.zillow.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        session.headers.update(headers)
        
        try:
            session.get("https://www.zillow.com/", timeout=30)
            time.sleep(2)
        except:
            pass
            
        return session
    
    def calculate_search_bounds(self):
        """Calculate search bounds from center point and radius"""
        center = self.config["search_area"]["center"]
        radius_miles = self.config["search_area"]["radius_miles"]
        
        # Get approximate coordinates for SF locations
        center_coords = self.get_approximate_coords(center)
        
        if not center_coords:
            print(f"⚠️  Using default bounds for '{center}'")
            return {"west": -122.45, "east": -122.38, "south": 37.74, "north": 37.78}
        
        lat, lng = center_coords
        
        # Convert miles to degrees
        lat_degree_miles = 69.0
        lng_degree_miles = 69.0 * math.cos(math.radians(lat))
        
        lat_offset = radius_miles / lat_degree_miles
        lng_offset = radius_miles / lng_degree_miles
        
        bounds = {
            "west": lng - lng_offset,
            "east": lng + lng_offset,
            "south": lat - lat_offset,
            "north": lat + lat_offset
        }
        
        print(f"🎯 Search area: {center}")
        print(f"📍 Radius: {radius_miles} miles")
        print(f"🗺️  Bounds: {bounds}")
        
        return bounds
    
    def get_approximate_coords(self, location):
        """Get approximate coordinates for common SF locations"""
        location_lower = location.lower()
        
        coords_map = {
            "mission district": (37.7599, -122.4148),
            "mission": (37.7599, -122.4148),
            "soma": (37.7749, -122.4194),
            "financial district": (37.7946, -122.4027),
            "castro": (37.7609, -122.4350),
            "noe valley": (37.7506, -122.4331),
            "bernal heights": (37.7405, -122.4155),
            "potrero hill": (37.7587, -122.4043),
            "hayes valley": (37.7767, -122.4244),
            "marina": (37.8021, -122.4416),
            "russian hill": (37.8014, -122.4156),
            "north beach": (37.8067, -122.4102),
            "sunset": (37.7431, -122.4661),
            "richmond": (37.7806, -122.4640),
            "pacific heights": (37.7919, -122.4370)
        }
        
        for key, coords in coords_map.items():
            if key in location_lower:
                return coords
        
        return (37.7599, -122.4148)  # Default to Mission District
    
    def get_search_payload(self, listing_type="for_sale", page=1):
        """Generate search payload for Zillow API"""
        center = self.config["search_area"]["center"]
        bounds = self.search_bounds
        
        base_payload = {
            "searchQueryState": {
                "pagination": {"currentPage": page},
                "usersSearchTerm": center,
                "mapBounds": bounds,
                "isMapVisible": True,
                "isListVisible": True,
                "mapZoom": 14,
                "filterState": {}
            },
            "wants": {
                "cat1": ["listResults", "mapResults"],
                "cat2": ["total"]
            },
            "requestId": page,
            "isDebugRequest": False
        }
        
        # Add filters
        filters = self.config["filters"]
        filter_state = {}
        
        # Price filters
        if filters.get("min_price") or filters.get("max_price"):
            price_filter = {}
            if filters.get("min_price"):
                price_filter["min"] = filters["min_price"]
            if filters.get("max_price"):
                price_filter["max"] = filters["max_price"]
            filter_state["price"] = price_filter
        
        # Square footage filters
        if filters.get("min_sqft") or filters.get("max_sqft"):
            sqft_filter = {}
            if filters.get("min_sqft"):
                sqft_filter["min"] = filters["min_sqft"]
            if filters.get("max_sqft"):
                sqft_filter["max"] = filters["max_sqft"]
            filter_state["sqft"] = sqft_filter
        
        # Listing type filters
        if listing_type == "sold":
            filter_state.update({
                "isForSaleByAgent": {"value": False},
                "isForSaleByOwner": {"value": False},
                "isNewConstruction": {"value": False},
                "isComingSoon": {"value": False},
                "isAuction": {"value": False},
                "isForSaleForeclosure": {"value": False},
                "isRecentlySold": {"value": True}
            })
        else:
            filter_state.update({
                "isForSaleByAgent": {"value": True},
                "isForSaleByOwner": {"value": True},
                "isNewConstruction": {"value": True},
                "isComingSoon": {"value": True},
                "isAuction": {"value": False},
                "isForSaleForeclosure": {"value": False}
            })
        
        base_payload["searchQueryState"]["filterState"] = filter_state
        return base_payload
    
    def fetch_properties(self, listing_type="for_sale"):
        """Fetch properties from Zillow API"""
        print(f"🔍 Searching for {listing_type} properties...")
        print(f"💰 Price range: ${self.config['filters']['min_price']:,} - ${self.config['filters']['max_price']:,}")
        print(f"📐 Size range: {self.config['filters']['min_sqft']:,} - {self.config['filters']['max_sqft']:,} sqft")
        
        endpoints = [
            "https://www.zillow.com/async-create-search-page-state",
            "https://www.zillow.com/search/search-results"
        ]
        
        all_properties = []
        
        for endpoint in endpoints:
            try:
                payload = self.get_search_payload(listing_type)
                time.sleep(random.uniform(2, 4))
                
                response = self.session.put(endpoint, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    properties = self.parse_properties(data, listing_type)
                    
                    if properties:
                        all_properties.extend(properties)
                        print(f"✅ Found {len(properties)} {listing_type} properties from {endpoint}")
                        break
                else:
                    print(f"❌ Status code: {response.status_code} for {endpoint}")
                    
            except Exception as e:
                print(f"❌ Error with {endpoint}: {e}")
                continue
        
        return all_properties
    
    def parse_properties(self, data, listing_type):
        """Parse property data from API response"""
        try:
            if 'cat1' in data:
                search_results = data['cat1'].get('searchResults', {})
            elif 'searchResults' in data:
                search_results = data['searchResults']
            else:
                return []
            
            map_results = search_results.get('mapResults', [])
            list_results = search_results.get('listResults', [])
            
            # Combine and deduplicate
            seen_zpids = set()
            unique_results = []
            for result in map_results + list_results:
                zpid = result.get('zpid')
                if zpid and zpid not in seen_zpids:
                    seen_zpids.add(zpid)
                    unique_results.append(result)
            
            # Extract property data
            properties = []
            for listing in unique_results:
                prop_data = self.extract_property_data(listing, listing_type)
                if prop_data:
                    properties.append(prop_data)
            
            return properties
            
        except Exception as e:
            print(f"Error parsing properties: {e}")
            return []
    
    def extract_property_data(self, listing, listing_type):
        """Extract comprehensive property data"""
        try:
            data = {
                'zpid': listing.get('zpid'),
                'listing_type': listing_type,
                'address': listing.get('address', 'N/A'),
                'price': None,
                'price_per_sqft': None,
                'beds': None,
                'baths': None,
                'sqft': None,
                'home_type': 'Unknown',
                'status': 'Unknown',
                'listed_date': None,
                'days_on_market': None,
                'broker': listing.get('brokerName', 'N/A'),
                'url': f"https://www.zillow.com{listing.get('detailUrl', '')}",
                'image_url': listing.get('imgSrc', ''),
                'latitude': None,
                'longitude': None,
                'lot_size': None,
                'year_built': None
            }
            
            # Extract coordinates
            data['latitude'] = listing.get('latLong', {}).get('latitude') or listing.get('lat')
            data['longitude'] = listing.get('latLong', {}).get('longitude') or listing.get('lng')
            
            # Extract detailed info
            if 'hdpData' in listing:
                home_info = listing['hdpData']['homeInfo']
                
                data.update({
                    'price': home_info.get('price'),
                    'beds': home_info.get('bedrooms'),
                    'baths': home_info.get('bathrooms'),
                    'sqft': home_info.get('livingArea'),
                    'home_type': home_info.get('homeType', 'Unknown'),
                    'status': home_info.get('homeStatus', 'Unknown'),
                    'lot_size': home_info.get('lotAreaValue'),
                    'year_built': home_info.get('yearBuilt')
                })
                
                # Extract listing date
                date_posted = home_info.get('datePosted')
                if date_posted:
                    try:
                        data['listed_date'] = datetime.fromtimestamp(date_posted / 1000).strftime("%Y-%m-%d")
                        listed_date = datetime.fromtimestamp(date_posted / 1000)
                        data['days_on_market'] = (datetime.now() - listed_date).days
                    except:
                        pass
            
            else:
                data.update({
                    'price': listing.get('price'),
                    'beds': listing.get('beds'),
                    'baths': listing.get('baths'),
                    'sqft': listing.get('area'),
                    'status': listing.get('statusText', 'Unknown')
                })
            
            # Calculate price per sqft
            if data['price'] and data['sqft'] and data['sqft'] > 0:
                data['price_per_sqft'] = round(data['price'] / data['sqft'], 0)
            
            # Apply filters
            if self.passes_criteria(data):
                return data
            
            return None
            
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return None
    
    def passes_criteria(self, data):
        """Check if property meets our criteria"""
        filters = self.config["filters"]
        
        # Price criteria
        if data['price']:
            if data['price'] < filters.get("min_price", 0):
                return False
            if data['price'] > filters.get("max_price", float('inf')):
                return False
        
        # Square footage criteria
        if data['sqft']:
            if data['sqft'] < filters.get("min_sqft", 0):
                return False
            if data['sqft'] > filters.get("max_sqft", float('inf')):
                return False
        
        return True
    
    def scan_market(self):
        """Main market scanning function"""
        print("🏠 Market Scanner Starting...")
        print("=" * 60)
        
        # Scan for-sale properties
        for_sale_properties = self.fetch_properties("for_sale")
        self.properties.extend(for_sale_properties)
        
        # Optionally scan sold properties
        if self.config["filters"]["include_sold"]:
            sold_properties = self.fetch_properties("sold")
            self.properties.extend(sold_properties)
        
        print(f"\n📊 Scan Results:")
        print(f"   Total properties found: {len(self.properties)}")
        
        if self.properties:
            # Sort by price per sqft
            self.properties.sort(key=lambda x: x.get('price_per_sqft', 0), reverse=True)
            
            # Show summary
            prices = [p['price'] for p in self.properties if p['price']]
            if prices:
                print(f"   Price range: ${min(prices):,} - ${max(prices):,}")
                print(f"   Average price: ${statistics.mean(prices):,.0f}")
                print(f"   Median price: ${statistics.median(prices):,.0f}")
        
        return len(self.properties) > 0
    
    def save_results(self):
        """Save results to both HTML and JSON files"""
        if not self.properties:
            print("⚠️  No properties to save")
            return
        
        # Save JSON data
        json_file = self.config["output"]["json_file"]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'config': self.config,
                'scan_date': datetime.now().isoformat(),
                'properties': self.properties,
                'summary': self.get_summary_stats()
            }, f, indent=2, default=str)
        
        print(f"✅ JSON data saved: {json_file}")
        
        # Generate HTML report
        html_file = self.generate_html_report()
        print(f"✅ HTML report generated: {html_file}")
        
        return html_file, json_file
    
    def get_summary_stats(self):
        """Generate summary statistics"""
        if not self.properties:
            return {}
        
        prices = [p['price'] for p in self.properties if p['price']]
        ppsqft = [p['price_per_sqft'] for p in self.properties if p['price_per_sqft']]
        sqft = [p['sqft'] for p in self.properties if p['sqft']]
        
        stats = {
            'total_properties': len(self.properties),
            'for_sale_count': len([p for p in self.properties if p['listing_type'] == 'for_sale']),
            'sold_count': len([p for p in self.properties if p['listing_type'] == 'sold'])
        }
        
        if prices:
            stats.update({
                'avg_price': statistics.mean(prices),
                'median_price': statistics.median(prices),
                'min_price': min(prices),
                'max_price': max(prices)
            })
        
        if ppsqft:
            stats.update({
                'avg_price_per_sqft': statistics.mean(ppsqft),
                'median_price_per_sqft': statistics.median(ppsqft),
                'min_price_per_sqft': min(ppsqft),
                'max_price_per_sqft': max(ppsqft)
            })
        
        if sqft:
            stats.update({
                'avg_sqft': statistics.mean(sqft),
                'median_sqft': statistics.median(sqft)
            })
        
        return stats
    
    def generate_html_report(self):
        """Generate beautiful HTML report"""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Scanner Results - {{SEARCH_AREA}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 1400px; margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center; margin-bottom: 40px; padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }
        .header h1 { font-size: 2.5em; color: #667eea; margin-bottom: 10px; }
        .header .subtitle { font-size: 1.2em; color: #666; margin-bottom: 15px; }
        .search-info {
            display: flex; justify-content: center; gap: 30px;
            flex-wrap: wrap; margin-top: 20px;
        }
        .search-info .info-item {
            background: #f8f9fa; padding: 10px 20px; border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .search-info .info-item strong { color: #667eea; }
        .summary-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 40px;
        }
        .summary-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px; border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-top: 4px solid #667eea;
        }
        .summary-card h3 { color: #667eea; margin-bottom: 20px; font-size: 1.3em; }
        .stat-item {
            display: flex; justify-content: space-between;
            margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 1px solid #dee2e6;
        }
        .stat-item:last-child { border-bottom: none; margin-bottom: 0; }
        .stat-item .label { color: #666; font-weight: 500; }
        .stat-item .value { font-weight: bold; color: #333; }
        .table-container {
            background: white; border-radius: 15px; overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-top: 30px;
        }
        .properties-table { width: 100%; border-collapse: collapse; }
        .properties-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 15px 10px; text-align: left; font-weight: 600;
            position: sticky; top: 0; z-index: 10;
        }
        .properties-table td {
            padding: 15px 10px; border-bottom: 1px solid #eee; vertical-align: middle;
        }
        .properties-table tbody tr:hover {
            background-color: #f8f9fa; transform: scale(1.01); transition: all 0.2s ease;
        }
        .property-photo {
            width: 80px; height: 60px; object-fit: cover; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .address-cell { max-width: 200px; word-wrap: break-word; }
        .price-cell { font-weight: bold; color: #28a745; }
        .ppsqft-cell { font-weight: 600; color: #667eea; }
        .status-badge {
            padding: 4px 12px; border-radius: 20px; font-size: 0.85em;
            font-weight: 600; text-transform: uppercase;
        }
        .status-badge.for-sale { background: #d4edda; color: #155724; }
        .status-badge.sold { background: #f8d7da; color: #721c24; }
        .view-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 8px 16px; border-radius: 20px;
            text-decoration: none; font-size: 0.9em; font-weight: 600;
            transition: all 0.3s ease;
        }
        .view-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        .footer {
            text-align: center; margin-top: 40px; padding-top: 20px;
            border-top: 1px solid #eee; color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Market Scanner Results</h1>
            <div class="subtitle">{{SEARCH_AREA}} • {{RADIUS}} mile radius</div>
            <div class="search-info">
                <div class="info-item"><strong>Price Range:</strong> {{PRICE_RANGE}}</div>
                <div class="info-item"><strong>Size Range:</strong> {{SIZE_RANGE}}</div>
                <div class="info-item"><strong>Properties Found:</strong> {{TOTAL_PROPERTIES}}</div>
                <div class="info-item"><strong>Generated:</strong> {{GENERATION_DATE}}</div>
            </div>
        </div>
        {{SUMMARY}}
        <div class="properties-section">
            <h2 style="color: #667eea; margin-bottom: 20px;">🏡 Property Listings</h2>
            {{PROPERTIES_TABLE}}
        </div>
        <div class="footer">
            <p>Generated by Market Scanner • Data from Zillow • <em>For informational purposes only</em></p>
        </div>
    </div>
</body>
</html>'''
        
        # Generate content sections
        summary_html = self.generate_summary_html()
        table_html = self.generate_properties_table()
        
        # Replace placeholders
        html = html_template.replace("{{SEARCH_AREA}}", self.config['search_area']['center'])
        html = html.replace("{{RADIUS}}", str(self.config['search_area']['radius_miles']))
        html = html.replace("{{GENERATION_DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html = html.replace("{{PRICE_RANGE}}", f"${self.config['filters']['min_price']:,} - ${self.config['filters']['max_price']:,}")
        html = html.replace("{{SIZE_RANGE}}", f"{self.config['filters']['min_sqft']:,} - {self.config['filters']['max_sqft']:,} sqft")
        html = html.replace("{{TOTAL_PROPERTIES}}", str(len(self.properties)))
        html = html.replace("{{SUMMARY}}", summary_html)
        html = html.replace("{{PROPERTIES_TABLE}}", table_html)
        
        # Write to file
        output_file = self.config["output"]["html_file"]
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def generate_summary_html(self):
        """Generate summary statistics HTML"""
        stats = self.get_summary_stats()
        if not stats:
            return "<p>No properties found matching criteria.</p>"
        
        html = f'''
        <div class="summary-grid">
            <div class="summary-card">
                <h3>📊 Overview</h3>
                <div class="stat-item">
                    <span class="label">Total Properties:</span>
                    <span class="value">{stats['total_properties']}</span>
                </div>
                <div class="stat-item">
                    <span class="label">For Sale:</span>
                    <span class="value">{stats['for_sale_count']}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Recently Sold:</span>
                    <span class="value">{stats['sold_count']}</span>
                </div>
            </div>
        '''
        
        if 'avg_price' in stats:
            html += f'''
            <div class="summary-card">
                <h3>💰 Price Analysis</h3>
                <div class="stat-item">
                    <span class="label">Average Price:</span>
                    <span class="value">${stats['avg_price']:,.0f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Median Price:</span>
                    <span class="value">${stats['median_price']:,.0f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Price Range:</span>
                    <span class="value">${stats['min_price']:,.0f} - ${stats['max_price']:,.0f}</span>
                </div>
            </div>
            '''
        
        if 'avg_price_per_sqft' in stats:
            html += f'''
            <div class="summary-card">
                <h3>📐 Price per Sqft</h3>
                <div class="stat-item">
                    <span class="label">Average $/sqft:</span>
                    <span class="value">${stats['avg_price_per_sqft']:,.0f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Median $/sqft:</span>
                    <span class="value">${stats['median_price_per_sqft']:,.0f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Range $/sqft:</span>
                    <span class="value">${stats['min_price_per_sqft']:,.0f} - ${stats['max_price_per_sqft']:,.0f}</span>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def generate_properties_table(self):
        """Generate properties table HTML"""
        if not self.properties:
            return "<p>No properties found.</p>"
        
        html = '''
        <div class="table-container">
            <table class="properties-table">
                <thead>
                    <tr>
                        <th>Photo</th>
                        <th>Address</th>
                        <th>Price</th>
                        <th>$/sqft</th>
                        <th>Beds</th>
                        <th>Baths</th>
                        <th>Sqft</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Days on Market</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for prop in self.properties:
            status_class = "for-sale" if prop['listing_type'] == 'for_sale' else "sold"
            
            html += f'''
                <tr class="{status_class}">
                    <td class="photo-cell">
                        <img src="{prop.get('image_url', '')}" alt="Property photo" class="property-photo" 
                             onerror="this.src='data:image/svg+xml,<svg xmlns=\\"http://www.w3.org/2000/svg\\" width=\\"80\\" height=\\"60\\" viewBox=\\"0 0 80 60\\"><rect width=\\"80\\" height=\\"60\\" fill=\\"#f0f0f0\\"/><text x=\\"40\\" y=\\"35\\" font-family=\\"Arial\\" font-size=\\"12\\" text-anchor=\\"middle\\" fill=\\"#999\\">No Image</text></svg>'">
                    </td>
                    <td class="address-cell">
                        <strong>{prop.get('address', 'N/A')}</strong>
                    </td>
                    <td class="price-cell">
                        <strong>${prop.get('price', 0):,}</strong>
                    </td>
                    <td class="ppsqft-cell">
                        ${prop.get('price_per_sqft', 0):,}
                    </td>
                    <td>{prop.get('beds', 'N/A')}</td>
                    <td>{prop.get('baths', 'N/A')}</td>
                    <td>{prop.get('sqft', 'N/A'):,}</td>
                    <td>{prop.get('home_type', 'Unknown')}</td>
                    <td class="status-cell">
                        <span class="status-badge {status_class}">{prop.get('status', 'Unknown')}</span>
                    </td>
                    <td>{prop.get('days_on_market', 'N/A')}</td>
                    <td class="actions-cell">
                        <a href="{prop.get('url', '#')}" target="_blank" class="view-btn">View</a>
                    </td>
                </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return html


def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Merge with defaults
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Ensure nested dicts are merged properly
        for key in ['search_area', 'filters', 'output']:
            if key in config:
                merged_config[key].update(config[key])
        
        return merged_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG


def create_sample_config(filename="config.json"):
    """Create a sample configuration file"""
    with open(filename, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print(f"✅ Sample config created: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Zillow Market Scanner")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--center", help="Search center (overrides config)")
    parser.add_argument("--radius", type=float, help="Search radius in miles (overrides config)")
    parser.add_argument("--create-config", action="store_true", help="Create sample configuration file")
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config(args.config)
        return
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print("Creating sample config...")
        create_sample_config(args.config)
        return
    
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.center:
        config["search_area"]["center"] = args.center
    if args.radius:
        config["search_area"]["radius_miles"] = args.radius
    
    # Create scanner and run
    scanner = MarketScanner(config)
    
    if scanner.scan_market():
        html_file, json_file = scanner.save_results()
        print(f"\n🎉 Market scan complete!")
        print(f"📄 HTML Report: {html_file}")
        print(f"📊 JSON Data: {json_file}")
        
        # Show top properties
        if scanner.properties:
            print(f"\n🏆 Top 5 Properties by Price per Sqft:")
            for i, prop in enumerate(scanner.properties[:5], 1):
                print(f"   {i}. {prop['address']} - ${prop['price']:,} (${prop.get('price_per_sqft', 0):,}/sqft)")
    else:
        print("❌ No properties found matching criteria")


if __name__ == "__main__":
    main()
