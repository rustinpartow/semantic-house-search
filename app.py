#!/usr/bin/env python3
"""app.py
Flask web application for Semantic House Search
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
try:
    from semantic_house_search import SemanticHouseSearch, load_config, DEFAULT_CONFIG
except ImportError as e:
    print(f"Warning: Could not import semantic_house_search: {e}")
    SemanticHouseSearch = None
    load_config = None
    DEFAULT_CONFIG = {}

import traceback

app = Flask(__name__)

# Global configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.route('/')
def index():
    """Main search page"""
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index.html: {e}")
        return jsonify({'error': f'Template error: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for semantic house search"""
    try:
        # Get search parameters from request
        data = request.get_json()
        
        # Extract parameters
        query = data.get('query', '')
        min_price = data.get('min_price', 1000000)
        max_price = data.get('max_price', 2000000)
        min_sqft = data.get('min_sqft', 1000)
        max_sqft = data.get('max_sqft', 2000)
        center = data.get('center', 'San Francisco, CA')
        radius = data.get('radius', 2.0)
        
        # Create configuration
        config = DEFAULT_CONFIG.copy()
        config.update({
            "search_area": {
                "center": center,
                "radius_miles": radius,
                "auto_bounds": True
            },
            "filters": {
                "min_price": min_price,
                "max_price": max_price,
                "min_sqft": min_sqft,
                "max_sqft": max_sqft,
                "home_types": ["CONDO", "SINGLE_FAMILY", "TOWNHOUSE"],
                "include_sold": False,
                "max_sold_age_months": 6
            },
            "semantic": {
                "enable_semantic_search": True,
                "semantic_weight": 0.3,
                "max_semantic_results": 100,
                "min_semantic_score": 0.0
            },
            "output": {
                "html_file": "temp_results.html",
                "json_file": "temp_results.json",
                "max_listings": 200
            }
        })
        
        # Create searcher and run search
        searcher = SemanticHouseSearch(config)
        success = searcher.search_properties(query)
        
        if success:
            # Prepare response data
            response_data = {
                'success': True,
                'query': query,
                'interpreted_filters': searcher.interpreted_filters,
                'properties': searcher.properties[:50],  # Limit to top 50 for API response
                'summary': searcher.get_summary_stats(),
                'search_date': datetime.now().isoformat()
            }
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': 'No properties found matching criteria',
                'query': query
            }), 404
            
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}',
            'query': query if 'query' in locals() else ''
        }), 500

@app.route('/api/neighborhoods')
def api_neighborhoods():
    """API endpoint to get supported neighborhoods"""
    neighborhoods = [
        "Mission District", "SOMA", "Financial District", "Castro", "Noe Valley",
        "Bernal Heights", "Potrero Hill", "Hayes Valley", "Marina", "Russian Hill",
        "North Beach", "Pacific Heights", "Sunset", "Richmond", "Cole Valley",
        "Alamo Square", "NOPA", "Haight", "Tenderloin", "Downtown"
    ]
    return jsonify(neighborhoods)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/debug/search', methods=['POST'])
def debug_search():
    """Debug endpoint to test search without full processing"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Test if semantic search module is working
        if SemanticHouseSearch is None:
            return jsonify({
                'error': 'SemanticHouseSearch module not available',
                'import_error': True
            }), 500
        
        # Test basic search functionality
        config = DEFAULT_CONFIG.copy()
        config.update({
            "search_area": {
                "center": "San Francisco, CA",
                "radius_miles": 2.0,
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
            "output": {
                "max_listings": 10  # Limit for testing
            }
        })
        
        searcher = SemanticHouseSearch(config)
        
        # Test basic search
        success = searcher.search_properties(query)
        
        return jsonify({
            'success': success,
            'query': query,
            'config': config,
            'searcher_created': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # For development
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
