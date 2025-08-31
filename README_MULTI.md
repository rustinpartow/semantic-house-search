# 🎯 Multi-Point Market Scanner

Enhanced Zillow market scanner with multiple search points and advanced filtering capabilities.

## 🚀 New Features

- **Multiple Search Points**: Define multiple (lat, lng, radius) search areas
- **Home Type Filtering**: Filter by specific property types (CONDO, SINGLE_FAMILY, etc.)
- **Smart Location Filtering**: Only includes properties actually within the defined search circles
- **Enhanced HTML Reports**: Beautiful reports showing multiple search areas
- **Command Line Point Override**: Specify search points directly in the command

## ✅ Your Test Results

**Search Points**: 
- Point 1: (37.771301, -122.431588) • 1 mile radius
- Point 2: (37.743336, -122.414442) • 0.5 mile radius

**Results**: 
- **41 properties found** (matching your criteria!)
- **Price range**: $1,023,000 - $1,988,888
- **Average price**: $1,368,851
- **Median price**: $1,298,000
- **Home types**: 25 condos + 16 single-family homes

## 🏠 Quick Start

### Run with Your Coordinates
```bash
python3 market_scanner_multi.py --points "[(37.771301, -122.431588, 1), (37.743336, -122.414442, 0.5)]"
```

### Create Custom Config
```bash
python3 market_scanner_multi.py --create-config
# Edit config_multi.json with your preferences
python3 market_scanner_multi.py
```

## ⚙️ Configuration

The `config_multi.json` supports:

```json
{
  "search_areas": {
    "points": [
      [37.771301, -122.431588, 1.0],
      [37.743336, -122.414442, 0.5]
    ],
    "description": "Hayes Valley + Bernal Heights"
  },
  "filters": {
    "min_price": 1000000,
    "max_price": 2000000,
    "min_sqft": 1000,
    "max_sqft": 2000,
    "home_types": ["CONDO", "SINGLE_FAMILY"],
    "include_sold": false,
    "max_sold_age_months": 6
  },
  "output": {
    "html_file": "market_scan_multi_results.html",
    "json_file": "market_scan_multi_data.json",
    "max_listings": 200
  }
}
```

## 🎯 Advanced Search Examples

### Multiple Neighborhoods
```bash
# Search 3 areas: Castro, Mission, Hayes Valley
python3 market_scanner_multi.py --points "[(37.7609, -122.4350, 0.3), (37.7599, -122.4148, 0.4), (37.7767, -122.4244, 0.3)]"
```

### Different Property Types
Edit the config to target specific types:
- `"home_types": ["CONDO"]` - Condos only
- `"home_types": ["SINGLE_FAMILY"]` - Houses only  
- `"home_types": ["CONDO", "SINGLE_FAMILY", "TOWNHOUSE"]` - Multiple types

### Price Ranges
- **Budget**: `"min_price": 800000, "max_price": 1200000`
- **Mid-range**: `"min_price": 1200000, "max_price": 1800000`
- **Luxury**: `"min_price": 1800000, "max_price": 3000000`

## 🔍 Understanding the Results

### Smart Location Filtering
Unlike the basic tool, this version:
- ✅ **Includes** properties within ANY of your search circles
- ❌ **Excludes** properties outside all search areas (even if in the bounding box)

### Property Data
Each property includes 20+ fields:
- Basic info (price, beds, baths, sqft)
- Location (exact lat/lng coordinates)
- Market data (price per sqft, days on market)
- Property details (home type, lot size, year built)
- Direct Zillow links

## 📊 Output Files

### `market_scan_multi_results.html`
Beautiful visual report with:
- Multiple search area display
- Home type breakdown
- Interactive property table
- Summary statistics

### `market_scan_multi_data.json`
Structured data perfect for:
- Custom analysis scripts
- Importing to spreadsheets
- Building dashboards
- Further filtering

## 🛠️ Advanced Usage

### Command Line Options
```bash
# Use custom config file
python3 market_scanner_multi.py --config my_search.json

# Override points from command line
python3 market_scanner_multi.py --points "[(lat,lng,radius), ...]"

# Create new config template
python3 market_scanner_multi.py --create-config
```

### Coordinate Finding
- Use Google Maps: Right-click → "What's here?"
- Use your existing tool's JSON output for interesting coordinates
- Target specific landmarks or intersections

## 💡 Next Steps for Fine Filtering

Your 41 properties are now ready for detailed analysis:

```python
# Example filtering ideas
import json

with open('market_scan_multi_data.json', 'r') as f:
    data = json.load(f)

properties = data['properties']

# Filter by price per sqft
good_deals = [p for p in properties if p['price_per_sqft'] < 1000]

# Filter by lot size (for outdoor space)
large_lots = [p for p in properties if p.get('lot_size', 0) > 2000]

# Filter by bedrooms
family_sized = [p for p in properties if p.get('beds', 0) >= 3]

# Filter by home type
condos_only = [p for p in properties if p['home_type'] == 'CONDO']
```

## 🎉 Success Metrics

The enhanced scanner found **41 properties** matching your exact criteria:
- ✅ Within your 2 search areas
- ✅ $1M-$2M price range
- ✅ 1K-2K sqft size
- ✅ Condos and single-family homes only
- ✅ Beautiful visual and data outputs

Perfect for your investment analysis workflow! 