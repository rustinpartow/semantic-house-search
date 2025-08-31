#!/usr/bin/env python3
"""
Generate HTML Report from Curated Property Data
"""

import json
from datetime import datetime

def generate_html_report(data_file, output_file):
    """Generate HTML report from curated data"""
    
    # Load curated data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    properties = data['properties']
    config = data['config']
    
    print(f"Generating report for {len(properties)} curated properties...")
    
    # Generate search points HTML
    search_points_html = ""
    for i, point in enumerate(config['search_areas']['points']):
        lat, lon, radius = point
        search_points_html += f'''
        <div class="point-item">
            <strong>Point {i+1}:</strong><br>
            Coordinates: {lat}, {lon}<br>
            Radius: {radius} mile{'s' if radius != 1 else ''}
        </div>'''
    
    # Generate summary statistics
    if properties:
        prices = [p['price'] for p in properties]
        sqfts = [p['sqft'] for p in properties]
        price_per_sqfts = [p['price_per_sqft'] for p in properties]
        
        summary_stats = {
            'total_properties': len(properties),
            'avg_price': sum(prices) / len(prices),
            'median_price': sorted(prices)[len(prices)//2],
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_sqft': sum(sqfts) / len(sqfts),
            'avg_price_per_sqft': sum(price_per_sqfts) / len(price_per_sqfts),
            'min_price_per_sqft': min(price_per_sqfts),
            'max_price_per_sqft': max(price_per_sqfts)
        }
        
        # Count by home type
        home_types = {}
        for prop in properties:
            home_type = prop['home_type']
            home_types[home_type] = home_types.get(home_type, 0) + 1
    else:
        summary_stats = {}
        home_types = {}
    
    # Generate summary HTML
    summary_html = f'''
    <div class="summary-grid">
        <div class="summary-card">
            <h3>📊 Price Statistics</h3>
            <div class="stat-item">
                <span class="label">Average Price:</span>
                <span class="value">${summary_stats.get('avg_price', 0):,.0f}</span>
            </div>
            <div class="stat-item">
                <span class="label">Median Price:</span>
                <span class="value">${summary_stats.get('median_price', 0):,.0f}</span>
            </div>
            <div class="stat-item">
                <span class="label">Price Range:</span>
                <span class="value">${summary_stats.get('min_price', 0):,.0f} - ${summary_stats.get('max_price', 0):,.0f}</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h3>📏 Size & Value</h3>
            <div class="stat-item">
                <span class="label">Average Size:</span>
                <span class="value">{summary_stats.get('avg_sqft', 0):,.0f} sqft</span>
            </div>
            <div class="stat-item">
                <span class="label">Avg Price/sqft:</span>
                <span class="value">${summary_stats.get('avg_price_per_sqft', 0):,.0f}</span>
            </div>
            <div class="stat-item">
                <span class="label">Price/sqft Range:</span>
                <span class="value">${summary_stats.get('min_price_per_sqft', 0):,.0f} - ${summary_stats.get('max_price_per_sqft', 0):,.0f}</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h3>🏠 Property Types</h3>
            {chr(10).join([f'<div class="stat-item"><span class="label">{home_type}:</span><span class="value">{count}</span></div>' for home_type, count in home_types.items()])}
        </div>
    </div>'''
    
    # Generate properties table
    table_rows = ""
    for prop in properties:
        status_class = 'for-sale' if prop['status'] == 'FOR_SALE' else 'sold'
        table_rows += f'''
        <tr>
            <td><img src="{prop['image_url']}" alt="Property" class="property-photo" onerror="this.style.display='none'"></td>
            <td class="address-cell">{prop['address']}</td>
            <td class="price-cell">${prop['price']:,.0f}</td>
            <td>{prop['beds']}</td>
            <td>{prop['baths']}</td>
            <td>{prop['sqft']:,.0f}</td>
            <td class="ppsqft-cell">${prop['price_per_sqft']:,.0f}</td>
            <td>{prop['home_type']}</td>
            <td><span class="status-badge {status_class}">{prop['status'].replace('_', ' ')}</span></td>
            <td><a href="{prop['url']}" target="_blank" class="view-btn">View</a></td>
        </tr>'''
    
    table_html = f'''
    <div class="table-container">
        <table class="properties-table">
            <thead>
                <tr>
                    <th>Photo</th>
                    <th>Address</th>
                    <th>Price</th>
                    <th>Beds</th>
                    <th>Baths</th>
                    <th>Sqft</th>
                    <th>$/Sqft</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Link</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>'''
    
    # Generate complete HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curated Property Results</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }}
        .container {{
            max-width: 1400px; margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }}
        .header {{
            text-align: center; margin-bottom: 40px; padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{ font-size: 2.5em; color: #667eea; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 1.2em; color: #666; margin-bottom: 15px; }}
        .search-info {{
            display: flex; justify-content: center; gap: 20px;
            flex-wrap: wrap; margin-top: 20px;
        }}
        .search-info .info-item {{
            background: #f8f9fa; padding: 10px 15px; border-radius: 10px;
            border-left: 4px solid #667eea; font-size: 0.9em;
        }}
        .search-info .info-item strong {{ color: #667eea; }}
        .search-points {{
            background: #e8f2ff; padding: 20px; border-radius: 15px;
            margin: 20px 0; border-left: 5px solid #667eea;
        }}
        .search-points h3 {{ color: #667eea; margin-bottom: 15px; }}
        .point-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }}
        .point-item {{
            background: white; padding: 10px; border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 40px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px; border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-top: 4px solid #667eea;
        }}
        .summary-card h3 {{ color: #667eea; margin-bottom: 20px; font-size: 1.3em; }}
        .stat-item {{
            display: flex; justify-content: space-between;
            margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        .stat-item:last-child {{ border-bottom: none; margin-bottom: 0; }}
        .stat-item .label {{ color: #666; font-weight: 500; }}
        .stat-item .value {{ font-weight: bold; color: #333; }}
        .table-container {{
            background: white; border-radius: 15px; overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-top: 30px;
        }}
        .properties-table {{ width: 100%; border-collapse: collapse; }}
        .properties-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 15px 10px; text-align: left; font-weight: 600;
            position: sticky; top: 0; z-index: 10;
        }}
        .properties-table td {{
            padding: 15px 10px; border-bottom: 1px solid #eee; vertical-align: middle;
        }}
        .properties-table tbody tr:hover {{
            background-color: #f8f9fa; transform: scale(1.01); transition: all 0.2s ease;
        }}
        .property-photo {{
            width: 80px; height: 60px; object-fit: cover; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .address-cell {{ max-width: 200px; word-wrap: break-word; }}
        .price-cell {{ font-weight: bold; color: #28a745; }}
        .ppsqft-cell {{ font-weight: 600; color: #667eea; }}
        .status-badge {{
            padding: 4px 12px; border-radius: 20px; font-size: 0.85em;
            font-weight: 600; text-transform: uppercase;
        }}
        .status-badge.for-sale {{ background: #d4edda; color: #155724; }}
        .status-badge.sold {{ background: #f8d7da; color: #721c24; }}
        .view-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 8px 16px; border-radius: 20px;
            text-decoration: none; font-size: 0.9em; font-weight: 600;
            transition: all 0.3s ease;
        }}
        .view-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }}
        .footer {{
            text-align: center; margin-top: 40px; padding-top: 20px;
            border-top: 1px solid #eee; color: #666;
        }}
        .curation-notice {{
            background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px;
            border-radius: 10px; margin: 20px 0; color: #0c5460;
        }}
        .curation-notice h4 {{ margin-bottom: 10px; color: #0c5460; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Curated Property Results</h1>
            <div class="subtitle">Manually filtered for parking availability and move-in ready condition</div>
            <div class="search-info">
                <div class="info-item"><strong>Price Range:</strong> ${config['filters']['min_price']:,} - ${config['filters']['max_price']:,}</div>
                <div class="info-item"><strong>Size Range:</strong> {config['filters']['min_sqft']:,} - {config['filters']['max_sqft']:,} sqft</div>
                <div class="info-item"><strong>Home Types:</strong> {', '.join(config['filters']['home_types'])}</div>
                <div class="info-item"><strong>Curated Properties:</strong> {len(properties)}</div>
                <div class="info-item"><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>
        
        <div class="curation-notice">
            <h4>🔍 Curation Process</h4>
            <p><strong>Original:</strong> 41 properties found → <strong>Removed:</strong> 23 properties with parking/renovation issues → <strong>Final:</strong> {len(properties)} quality properties</p>
            <p><strong>Filtered out:</strong> Apartment units with uncertain parking, properties with only 1 bathroom, fixer-uppers with very low $/sqft, and properties with small lots.</p>
        </div>
        
        <div class="search-points">
            <h3>📍 Search Areas</h3>
            <div class="point-list">{search_points_html}</div>
        </div>
        
        {summary_html}
        
        <div class="properties-section">
            <h2 style="color: #667eea; margin-bottom: 20px;">🏡 Curated Property Listings</h2>
            {table_html}
        </div>
        
        <div class="footer">
            <p>🏡 Curated Property Market Report | Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
            <p>Properties manually filtered for parking availability and move-in ready condition</p>
        </div>
    </div>
</body>
</html>'''
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Curated HTML report saved to: {output_file}")
    return output_file

if __name__ == '__main__':
    generate_html_report('market_scan_multi_data_curated.json', 'market_scan_curated_results.html') 