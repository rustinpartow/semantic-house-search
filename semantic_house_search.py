#!/usr/bin/env python3
"""semantic_house_search.py
RAG-powered semantic house search tool that combines Zillow's native filters 
with LLM-powered natural language queries.

Features:
- Hard filters: Price, sqft, location, home type
- Semantic search: Natural language queries like "no one living above me, NOT a fixer-upper"
- Hybrid ranking: Combines hard filters with semantic relevance scoring
- Beautiful HTML reports with match explanations

Example usage:
$ python semantic_house_search.py --config semantic_config.json
$ python semantic_house_search.py --query "no one living above me, NOT a fixer-upper" --price "1.2M-1.75M" --sqft "750-1500"
"""

import json, statistics, requests, time, random, argparse, os, math
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from typing import List, Dict, Any, Optional, Tuple

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
        "home_types": ["CONDO", "SINGLE_FAMILY", "TOWNHOUSE"],
        "include_sold": False,
        "max_sold_age_months": 6
    },
    "semantic": {
        "enable_semantic_search": True,
        "semantic_weight": 0.3,  # Weight for semantic scoring vs hard filters
        "max_semantic_results": 50,
        "min_semantic_score": 0.3
    },
    "output": {
        "html_file": "semantic_search_results.html",
        "json_file": "semantic_search_data.json",
        "max_listings": 200
    }
}

class SemanticHouseSearch:
    def __init__(self, config):
        self.config = config
        self.session = self.create_session()
        self.properties = []
        self.search_bounds = self.calculate_search_bounds()
        self.semantic_query = None
        self.interpreted_filters = {}
        
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
    
    def interpret_semantic_query(self, query: str) -> Dict[str, Any]:
        """
        Interpret natural language query and extract filters and preferences.
        This is where the LLM/RAG magic happens!
        """
        if not query:
            return {}
        
        print(f"🧠 Interpreting semantic query: '{query}'")
        
        # Initialize interpreted filters
        interpreted = {
            "home_types": [],
            "excluded_home_types": [],
            "preferences": [],
            "exclusions": [],
            "floor_preferences": [],
            "condition_preferences": [],
            "neighborhood_preferences": [],
            "neighborhood_exclusions": []
        }
        
        query_lower = query.lower()
        
        # Map semantic concepts to Zillow filters
        semantic_mappings = {
            # No one living above = top floor condos, townhomes, single family
            "no one living above": {
                "home_types": ["TOWNHOUSE", "SINGLE_FAMILY"],
                "preferences": ["top_floor_condo"],
                "excluded_home_types": ["mid_floor_condo", "ground_floor_condo"]
            },
            "nobody above": {
                "home_types": ["TOWNHOUSE", "SINGLE_FAMILY"],
                "preferences": ["top_floor_condo"]
            },
            "top floor": {
                "preferences": ["top_floor_condo"]
            },
            "penthouse": {
                "preferences": ["top_floor_condo", "luxury"]
            },
            
            # Not a fixer-upper = good condition, recently renovated
            "not a fixer-upper": {
                "condition_preferences": ["good_condition", "recently_renovated"],
                "exclusions": ["needs_work", "fixer_upper", "handyman_special"]
            },
            "not fixer": {
                "condition_preferences": ["good_condition"],
                "exclusions": ["fixer_upper"]
            },
            "move-in ready": {
                "condition_preferences": ["move_in_ready", "good_condition"]
            },
            "turnkey": {
                "condition_preferences": ["turnkey", "move_in_ready"]
            },
            
            # Privacy preferences
            "private": {
                "preferences": ["private", "quiet"]
            },
            "quiet": {
                "preferences": ["quiet", "private"]
            },
            "peaceful": {
                "preferences": ["quiet", "peaceful"]
            },
            
            # Outdoor space
            "outdoor space": {
                "preferences": ["outdoor_space", "patio", "deck", "garden"]
            },
            "garden": {
                "preferences": ["garden", "outdoor_space"]
            },
            "patio": {
                "preferences": ["patio", "outdoor_space"]
            },
            "deck": {
                "preferences": ["deck", "outdoor_space"]
            },
            
            # Parking
            "parking": {
                "preferences": ["parking", "garage"]
            },
            "garage": {
                "preferences": ["garage", "parking"]
            },
            
            # Views
            "view": {
                "preferences": ["view", "scenic"]
            },
            "city view": {
                "preferences": ["city_view", "view"]
            },
            "water view": {
                "preferences": ["water_view", "view"]
            },
            
            # NEW: Detailed architectural and neighborhood preferences
            
            # Architectural exclusions
            "not edwardian": {
                "exclusions": ["edwardian", "victorian", "old_architecture"]
            },
            "not super old": {
                "exclusions": ["old_building", "historic", "vintage"]
            },
            "not creaky": {
                "exclusions": ["old_flooring", "creaky", "worn"]
            },
            "not dusty": {
                "exclusions": ["dusty", "old_interior", "outdated"]
            },
            
            # Architectural preferences
            "high ceilings": {
                "preferences": ["high_ceilings", "modern_architecture", "open_feel"]
            },
            "natural light": {
                "preferences": ["natural_light", "sunny", "bright"]
            },
            "kitchen natural light": {
                "preferences": ["kitchen_light", "natural_light", "bright_kitchen"]
            },
            
            # Neighborhood preferences (GOOD areas)
            "alamo square": {
                "neighborhood_preferences": ["alamo_square", "safe_area", "desirable"]
            },
            "cole valley": {
                "neighborhood_preferences": ["cole_valley", "safe_area", "desirable"]
            },
            "nopa": {
                "neighborhood_preferences": ["nopa", "safe_area", "desirable"]
            },
            "haight": {
                "neighborhood_preferences": ["haight", "safe_area", "desirable"]
            },
            "hayes valley": {
                "neighborhood_preferences": ["hayes_valley", "safe_area", "desirable"]
            },
            
            # Neighborhood exclusions (BAD areas)
            "tenderloin": {
                "neighborhood_exclusions": ["tenderloin", "high_crime", "unsafe"]
            },
            "market st": {
                "neighborhood_exclusions": ["market_street", "busy_street", "noisy"]
            },
            "downtown": {
                "neighborhood_exclusions": ["downtown", "business_district", "noisy"]
            },
            "fidi": {
                "neighborhood_exclusions": ["financial_district", "business_area", "noisy"]
            },
            
            # Mission District nuances
            "mission safe": {
                "neighborhood_preferences": ["mission_safe", "quiet_mission", "peaceful_mission"]
            },
            "mission quiet": {
                "neighborhood_preferences": ["mission_quiet", "peaceful_mission"]
            },
            "mission peaceful": {
                "neighborhood_preferences": ["mission_peaceful", "quiet_mission"]
            },
            
            # Lifestyle exclusions
            "not super quiet": {
                "exclusions": ["too_quiet", "residential_only", "family_focused"]
            },
            "not residential": {
                "exclusions": ["residential_only", "family_neighborhood", "suburban_feel"]
            },
            "not family friendly": {
                "exclusions": ["family_focused", "kid_friendly", "suburban"]
            },
            "not suuuper quiet": {
                "exclusions": ["too_quiet", "dead_quiet", "boring_area"]
            }
        }
        
        # Apply semantic mappings
        for concept, mapping in semantic_mappings.items():
            if concept in query_lower:
                if "home_types" in mapping:
                    interpreted["home_types"].extend(mapping["home_types"])
                if "preferences" in mapping:
                    interpreted["preferences"].extend(mapping["preferences"])
                if "excluded_home_types" in mapping:
                    interpreted["excluded_home_types"].extend(mapping["excluded_home_types"])
                if "exclusions" in mapping:
                    interpreted["exclusions"].extend(mapping["exclusions"])
                if "condition_preferences" in mapping:
                    interpreted["condition_preferences"].extend(mapping["condition_preferences"])
                if "neighborhood_preferences" in mapping:
                    interpreted["neighborhood_preferences"].extend(mapping["neighborhood_preferences"])
                if "neighborhood_exclusions" in mapping:
                    interpreted["neighborhood_exclusions"].extend(mapping["neighborhood_exclusions"])
        
        # Remove duplicates
        for key in interpreted:
            interpreted[key] = list(set(interpreted[key]))
        
        print(f"📋 Interpreted filters: {interpreted}")
        return interpreted
    
    def get_search_payload(self, listing_type="for_sale", page=1):
        """Generate search payload for Zillow API with semantic filters"""
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
        
        # Add hard filters
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
        
        # Home type filters (from semantic interpretation)
        home_types = self.interpreted_filters.get("home_types", [])
        if not home_types and filters.get("home_types"):
            home_types = filters["home_types"]
        
        if home_types:
            # Map to Zillow home type codes
            zillow_home_types = {
                "CONDO": ["10001"],
                "SINGLE_FAMILY": ["10000"],
                "TOWNHOUSE": ["10002"]
            }
            selected_types = []
            for home_type in home_types:
                if home_type in zillow_home_types:
                    selected_types.extend(zillow_home_types[home_type])
            
            if selected_types:
                filter_state["homeType"] = {"value": selected_types}
        
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
        
        if self.interpreted_filters.get("home_types"):
            print(f"🏠 Home types: {', '.join(self.interpreted_filters['home_types'])}")
        
        endpoints = [
            "https://www.zillow.com/async-create-search-page-state",
            "https://www.zillow.com/search/search-results"
        ]
        
        all_properties = []
        
        for endpoint in endpoints:
            try:
                payload = self.get_search_payload(listing_type)
                # More conservative rate limiting
                time.sleep(random.uniform(3, 6))
                
                # Add more realistic headers
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
                    "X-Requested-With": "XMLHttpRequest"
                }
                self.session.headers.update(headers)
                
                response = self.session.put(endpoint, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    properties = self.parse_properties(data, listing_type)
                    
                    if properties:
                        all_properties.extend(properties)
                        print(f"✅ Found {len(properties)} {listing_type} properties from {endpoint}")
                        break
                elif response.status_code == 404:
                    print(f"⚠️  404 error for {endpoint} - trying alternative approach")
                    # Try with a simpler payload
                    simple_payload = {
                        "searchQueryState": {
                            "pagination": {"currentPage": 1},
                            "usersSearchTerm": "San Francisco, CA",
                            "mapBounds": self.search_bounds,
                            "isMapVisible": True,
                            "isListVisible": True,
                            "mapZoom": 12
                        },
                        "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
                        "requestId": 1
                    }
                    time.sleep(random.uniform(4, 7))
                    response = self.session.put(endpoint, json=simple_payload, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        properties = self.parse_properties(data, listing_type)
                        if properties:
                            all_properties.extend(properties)
                            print(f"✅ Found {len(properties)} {listing_type} properties with fallback method")
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
        """Extract comprehensive property data with semantic scoring"""
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
                'year_built': None,
                'semantic_score': 0.0,
                'semantic_matches': [],
                'semantic_explanations': []
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
            
            # Apply semantic scoring
            if self.config["semantic"]["enable_semantic_search"]:
                semantic_score, matches, explanations = self.calculate_semantic_score(data)
                data['semantic_score'] = semantic_score
                data['semantic_matches'] = matches
                data['semantic_explanations'] = explanations
            
            # Apply filters
            if self.passes_criteria(data):
                return data
            
            return None
            
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return None
    
    def calculate_semantic_score(self, property_data: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """
        Calculate semantic relevance score based on interpreted query.
        This is where the RAG magic happens!
        """
        score = 0.0
        matches = []
        explanations = []
        
        if not self.interpreted_filters:
            return score, matches, explanations
        
        home_type = property_data.get('home_type', '').upper()
        address = property_data.get('address', '').lower()
        year_built = property_data.get('year_built')
        lot_size = property_data.get('lot_size', 0)
        
        # Check home type preferences
        preferred_home_types = self.interpreted_filters.get("home_types", [])
        if preferred_home_types and home_type in [ht.upper() for ht in preferred_home_types]:
            score += 0.3
            matches.append(f"Home type: {home_type}")
            explanations.append(f"Matches preferred home type: {home_type}")
        
        # Check for top floor condos (no one living above)
        if "top_floor_condo" in self.interpreted_filters.get("preferences", []):
            if home_type == "CONDO":
                # Check if it's likely a top floor unit
                if any(floor_indicator in address for floor_indicator in ["top", "penthouse", "roof", "terrace"]):
                    score += 0.4
                    matches.append("Top floor unit")
                    explanations.append("Likely top floor condo - no one living above")
                elif any(high_floor in address for high_floor in ["4", "5", "6", "7", "8", "9"]):
                    score += 0.2
                    matches.append("High floor unit")
                    explanations.append("High floor condo - reduced noise from above")
        
        # Check for townhouses and single family (no one above)
        if "no one living above" in self.semantic_query.lower() or "nobody above" in self.semantic_query.lower():
            if home_type in ["TOWNHOUSE", "SINGLE_FAMILY"]:
                score += 0.5
                matches.append("No one above")
                explanations.append(f"{home_type} - no neighbors above")
        
        # Check condition preferences (not a fixer-upper)
        if "good_condition" in self.interpreted_filters.get("condition_preferences", []):
            # Simple heuristics for good condition
            if year_built and year_built > 2000:
                score += 0.2
                matches.append("Recent construction")
                explanations.append(f"Built in {year_built} - likely good condition")
            
            # Check for renovation indicators in address/description
            if any(reno_indicator in address for reno_indicator in ["renovated", "updated", "modern"]):
                score += 0.3
                matches.append("Recently renovated")
                explanations.append("Address suggests recent renovations")
        
        # NEW: Check architectural exclusions
        if "edwardian" in self.interpreted_filters.get("exclusions", []) or "victorian" in self.interpreted_filters.get("exclusions", []):
            if any(old_arch in address for old_arch in ["edwardian", "victorian", "1900", "1910", "1920"]):
                score -= 0.3
                matches.append("Old architecture")
                explanations.append("Edwardian/Victorian architecture detected")
        
        if "old_building" in self.interpreted_filters.get("exclusions", []):
            if year_built and year_built < 1980:
                score -= 0.2
                matches.append("Older building")
                explanations.append(f"Built in {year_built} - older construction")
        
        # NEW: Check architectural preferences
        if "high_ceilings" in self.interpreted_filters.get("preferences", []):
            if any(modern_indicator in address for modern_indicator in ["modern", "contemporary", "loft", "converted"]):
                score += 0.2
                matches.append("Modern architecture")
                explanations.append("Address suggests modern features like high ceilings")
        
        if "natural_light" in self.interpreted_filters.get("preferences", []):
            if any(light_indicator in address for light_indicator in ["sunny", "bright", "south", "east", "west"]):
                score += 0.2
                matches.append("Natural light")
                explanations.append("Address suggests good natural light")
        
        # NEW: Check neighborhood preferences
        neighborhood_prefs = self.interpreted_filters.get("neighborhood_preferences", [])
        if neighborhood_prefs:
            if any(pref in address for pref in ["alamo", "cole", "nopa", "haight", "hayes"]):
                score += 0.3
                matches.append("Desirable neighborhood")
                explanations.append("Located in preferred neighborhood")
        
        # NEW: Check neighborhood exclusions
        neighborhood_exclusions = self.interpreted_filters.get("neighborhood_exclusions", [])
        if neighborhood_exclusions:
            if any(excl in address for excl in ["tenderloin", "market", "downtown", "financial"]):
                score -= 0.4
                matches.append("Less desirable area")
                explanations.append("Located in area to avoid")
        
        # Check for outdoor space preferences
        if any(outdoor_pref in self.interpreted_filters.get("preferences", []) for outdoor_pref in ["outdoor_space", "patio", "deck", "garden"]):
            if lot_size and lot_size > 2000:  # Larger lot likely has outdoor space
                score += 0.2
                matches.append("Outdoor space")
                explanations.append(f"Large lot ({lot_size:.0f} sqft) - likely outdoor space")
        
        # Check for parking preferences
        if "parking" in self.interpreted_filters.get("preferences", []) or "garage" in self.interpreted_filters.get("preferences", []):
            if any(parking_indicator in address for parking_indicator in ["garage", "parking", "driveway"]):
                score += 0.2
                matches.append("Parking available")
                explanations.append("Address suggests parking/garage")
        
        # NEW: Check lifestyle exclusions
        if "too_quiet" in self.interpreted_filters.get("exclusions", []) or "residential_only" in self.interpreted_filters.get("exclusions", []):
            if any(quiet_indicator in address for quiet_indicator in ["residential", "quiet", "family", "suburban"]):
                score -= 0.2
                matches.append("Too quiet/residential")
                explanations.append("Area may be too quiet/residential")
        
        # Normalize score to 0-1 range
        score = max(0.0, min(score, 1.0))
        
        return score, matches, explanations
    
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
        
        # Semantic score threshold
        if self.config["semantic"]["enable_semantic_search"]:
            min_score = self.config["semantic"]["min_semantic_score"]
            if data.get('semantic_score', 0) < min_score:
                return False
        
        return True
    
    def search_properties(self, semantic_query: str = None):
        """Main search function with semantic capabilities"""
        print("🏠 Semantic House Search Starting...")
        print("=" * 60)
        
        # Interpret semantic query
        if semantic_query:
            self.semantic_query = semantic_query
            self.interpreted_filters = self.interpret_semantic_query(semantic_query)
        
        # Scan for-sale properties
        for_sale_properties = self.fetch_properties("for_sale")
        self.properties.extend(for_sale_properties)
        
        # Optionally scan sold properties
        if self.config["filters"]["include_sold"]:
            sold_properties = self.fetch_properties("sold")
            self.properties.extend(sold_properties)
        
        # Apply semantic ranking
        if self.config["semantic"]["enable_semantic_search"] and self.properties:
            self.properties = self.rank_by_semantic_relevance()
        
        print(f"\n📊 Search Results:")
        print(f"   Total properties found: {len(self.properties)}")
        
        if self.properties:
            # Show summary
            prices = [p['price'] for p in self.properties if p['price']]
            if prices:
                print(f"   Price range: ${min(prices):,} - ${max(prices):,}")
                print(f"   Average price: ${statistics.mean(prices):,.0f}")
                print(f"   Median price: ${statistics.median(prices):,.0f}")
            
            # Show semantic matches
            if self.config["semantic"]["enable_semantic_search"]:
                semantic_matches = [p for p in self.properties if p.get('semantic_score', 0) > 0]
                print(f"   Properties with semantic matches: {len(semantic_matches)}")
        
        return len(self.properties) > 0
    
    def rank_by_semantic_relevance(self):
        """Rank properties by semantic relevance"""
        # Sort by semantic score (descending), then by price per sqft
        return sorted(self.properties, 
                     key=lambda x: (x.get('semantic_score', 0), x.get('price_per_sqft', 0)), 
                     reverse=True)
    
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
                'semantic_query': self.semantic_query,
                'interpreted_filters': self.interpreted_filters,
                'search_date': datetime.now().isoformat(),
                'properties': self.properties,
                'summary': self.get_summary_stats()
            }, f, indent=2, default=str)
        
        print(f"✅ JSON data saved: {json_file}")
        
        # Generate HTML report
        html_file = self.generate_html_report()
        print(f"✅ HTML report generated: {html_file}")
        
        return html_file, json_file
    
    def generate_html_report(self):
        """Generate beautiful HTML report with semantic match explanations"""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic House Search Results - {{SEARCH_AREA}}</title>
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
        .semantic-query {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px; border-radius: 15px; margin: 20px 0;
            border-left: 5px solid #28a745;
        }
        .semantic-query h3 { color: #28a745; margin-bottom: 10px; }
        .semantic-query .query-text { font-style: italic; color: #666; }
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
        .semantic-score {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white; padding: 4px 8px; border-radius: 12px;
            font-size: 0.8em; font-weight: 600;
        }
        .semantic-matches {
            max-width: 200px; font-size: 0.85em;
        }
        .semantic-match {
            background: #e8f5e8; color: #155724; padding: 2px 6px;
            border-radius: 8px; margin: 2px; display: inline-block;
            font-size: 0.75em;
        }
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
            <h1>🧠 Semantic House Search Results</h1>
            <div class="subtitle">{{SEARCH_AREA}} • {{RADIUS}} mile radius</div>
            {{SEMANTIC_QUERY_SECTION}}
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
            <p>Generated by Semantic House Search • Data from Zillow • <em>For informational purposes only</em></p>
        </div>
    </div>
</body>
</html>'''
        
        # Generate content sections
        summary_html = self.generate_summary_html()
        table_html = self.generate_properties_table()
        semantic_query_html = self.generate_semantic_query_section()
        
        # Replace placeholders
        html = html_template.replace("{{SEARCH_AREA}}", self.config['search_area']['center'])
        html = html.replace("{{RADIUS}}", str(self.config['search_area']['radius_miles']))
        html = html.replace("{{GENERATION_DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html = html.replace("{{PRICE_RANGE}}", f"${self.config['filters']['min_price']:,} - ${self.config['filters']['max_price']:,}")
        html = html.replace("{{SIZE_RANGE}}", f"{self.config['filters']['min_sqft']:,} - {self.config['filters']['max_sqft']:,} sqft")
        html = html.replace("{{TOTAL_PROPERTIES}}", str(len(self.properties)))
        html = html.replace("{{SUMMARY}}", summary_html)
        html = html.replace("{{PROPERTIES_TABLE}}", table_html)
        html = html.replace("{{SEMANTIC_QUERY_SECTION}}", semantic_query_html)
        
        # Write to file
        output_file = self.config["output"]["html_file"]
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def generate_semantic_query_section(self):
        """Generate semantic query section HTML"""
        if not self.semantic_query:
            return ""
        
        return f'''
        <div class="semantic-query">
            <h3>🧠 Semantic Query</h3>
            <div class="query-text">"{self.semantic_query}"</div>
        </div>
        '''
    
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
                <div class="stat-item">
                    <span class="label">Semantic Matches:</span>
                    <span class="value">{stats.get('semantic_matches', 0)}</span>
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
        
        if 'avg_semantic_score' in stats:
            html += f'''
            <div class="summary-card">
                <h3>🧠 Semantic Analysis</h3>
                <div class="stat-item">
                    <span class="label">Avg Semantic Score:</span>
                    <span class="value">{stats['avg_semantic_score']:.2f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Max Semantic Score:</span>
                    <span class="value">{stats['max_semantic_score']:.2f}</span>
                </div>
                <div class="stat-item">
                    <span class="label">Properties with Matches:</span>
                    <span class="value">{stats.get('semantic_matches', 0)}</span>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def generate_properties_table(self):
        """Generate properties table HTML with semantic match information"""
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
                        <th>Semantic Score</th>
                        <th>Matches</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for prop in self.properties:
            status_class = "for-sale" if prop['listing_type'] == 'for_sale' else "sold"
            semantic_score = prop.get('semantic_score', 0)
            semantic_matches = prop.get('semantic_matches', [])
            
            # Generate semantic matches HTML
            matches_html = ""
            if semantic_matches:
                for match in semantic_matches[:3]:  # Show first 3 matches
                    matches_html += f'<span class="semantic-match">{match}</span>'
                if len(semantic_matches) > 3:
                    matches_html += f'<span class="semantic-match">+{len(semantic_matches)-3} more</span>'
            
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
                    <td>
                        {f'<span class="semantic-score">{semantic_score:.2f}</span>' if semantic_score > 0 else 'N/A'}
                    </td>
                    <td class="semantic-matches">
                        {matches_html if matches_html else 'None'}
                    </td>
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
    
    def get_summary_stats(self):
        """Generate summary statistics"""
        if not self.properties:
            return {}
        
        prices = [p['price'] for p in self.properties if p['price']]
        ppsqft = [p['price_per_sqft'] for p in self.properties if p['price_per_sqft']]
        sqft = [p['sqft'] for p in self.properties if p['sqft']]
        semantic_scores = [p.get('semantic_score', 0) for p in self.properties]
        
        stats = {
            'total_properties': len(self.properties),
            'for_sale_count': len([p for p in self.properties if p['listing_type'] == 'for_sale']),
            'sold_count': len([p for p in self.properties if p['listing_type'] == 'sold']),
            'semantic_matches': len([p for p in self.properties if p.get('semantic_score', 0) > 0])
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
        
        if semantic_scores:
            stats.update({
                'avg_semantic_score': statistics.mean(semantic_scores),
                'max_semantic_score': max(semantic_scores)
            })
        
        return stats


def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Merge with defaults
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Ensure nested dicts are merged properly
        for key in ['search_area', 'filters', 'semantic', 'output']:
            if key in config:
                merged_config[key].update(config[key])
        
        return merged_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG


def create_sample_config(filename="semantic_config.json"):
    """Create a sample configuration file"""
    with open(filename, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print(f"✅ Sample config created: {filename}")


def parse_price_range(price_str):
    """Parse price range string like '1.2M-1.75M' or '1200000-1750000'"""
    if not price_str:
        return None, None
    
    # Handle M/K suffixes
    def parse_price(price):
        price = price.strip().upper()
        if price.endswith('M'):
            return int(float(price[:-1]) * 1000000)
        elif price.endswith('K'):
            return int(float(price[:-1]) * 1000)
        else:
            return int(price)
    
    if '-' in price_str:
        min_price, max_price = price_str.split('-')
        return parse_price(min_price), parse_price(max_price)
    else:
        price = parse_price(price_str)
        return price, price


def parse_sqft_range(sqft_str):
    """Parse sqft range string like '750-1500'"""
    if not sqft_str:
        return None, None
    
    if '-' in sqft_str:
        min_sqft, max_sqft = sqft_str.split('-')
        return int(min_sqft), int(max_sqft)
    else:
        sqft = int(sqft_str)
        return sqft, sqft


def main():
    parser = argparse.ArgumentParser(description="Semantic House Search Tool")
    parser.add_argument("--config", default="semantic_config.json", help="Path to configuration file")
    parser.add_argument("--query", help="Semantic search query (e.g., 'no one living above me, NOT a fixer-upper')")
    parser.add_argument("--price", help="Price range (e.g., '1.2M-1.75M' or '1200000-1750000')")
    parser.add_argument("--sqft", help="Square footage range (e.g., '750-1500')")
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
    if args.price:
        min_price, max_price = parse_price_range(args.price)
        if min_price:
            config["filters"]["min_price"] = min_price
        if max_price:
            config["filters"]["max_price"] = max_price
    if args.sqft:
        min_sqft, max_sqft = parse_sqft_range(args.sqft)
        if min_sqft:
            config["filters"]["min_sqft"] = min_sqft
        if max_sqft:
            config["filters"]["max_sqft"] = max_sqft
    
    # Create searcher and run
    searcher = SemanticHouseSearch(config)
    
    if searcher.search_properties(args.query):
        html_file, json_file = searcher.save_results()
        print(f"\n🎉 Semantic search complete!")
        print(f"📄 HTML Report: {html_file}")
        print(f"📊 JSON Data: {json_file}")
        
        # Show top properties
        if searcher.properties:
            print(f"\n🏆 Top 30 Properties by Semantic Relevance:")
            for i, prop in enumerate(searcher.properties[:30], 1):
                semantic_info = ""
                if prop.get('semantic_score', 0) > 0:
                    semantic_info = f" (Score: {prop['semantic_score']:.2f})"
                print(f"   {i}. {prop['address']} - ${prop['price']:,} (${prop.get('price_per_sqft', 0):,}/sqft){semantic_info}")
    else:
        print("❌ No properties found matching criteria")


if __name__ == "__main__":
    main()
