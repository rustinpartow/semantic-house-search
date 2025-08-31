# 🧠 Semantic House Search

RAG-powered semantic house search tool that combines Zillow's native filters with LLM-powered natural language queries.

## Features

- **🎯 Hard Filters**: Price, square footage, location, home type
- **🧠 Semantic Search**: Natural language queries like "no one living above me, NOT a fixer-upper"
- **🔄 Hybrid Ranking**: Combines hard filters with semantic relevance scoring
- **📊 Beautiful Reports**: HTML reports with semantic match explanations
- **🏠 Smart Interpretation**: Automatically maps natural language to Zillow filters

## Quick Start

### 1. Install Dependencies
```bash
pip install requests beautifulsoup4
```

### 2. Run with Semantic Query
```bash
# Example: Find properties with no one living above, not a fixer-upper
python semantic_house_search.py --query "no one living above me, NOT a fixer-upper" --price "1.2M-1.75M" --sqft "750-1500"

# Or use a config file
python semantic_house_search.py --config semantic_config.json
```

### 3. View Results
- Open `semantic_search_results.html` in your browser for the visual report
- Check `semantic_search_data.json` for structured data

## Semantic Query Examples

The tool understands natural language queries and maps them to property characteristics:

### Privacy & Noise
- **"no one living above me"** → Townhomes, single family homes, top floor condos
- **"nobody above"** → Same as above
- **"quiet"** → Properties in quieter areas
- **"private"** → Properties with privacy features

### Condition & Move-in Ready
- **"NOT a fixer-upper"** → Good condition, recently renovated properties
- **"not fixer"** → Same as above
- **"move-in ready"** → Turnkey properties
- **"turnkey"** → Ready to move in

### Outdoor Space
- **"outdoor space"** → Properties with patios, decks, gardens
- **"garden"** → Properties with garden space
- **"patio"** → Properties with patios
- **"deck"** → Properties with decks

### Parking & Amenities
- **"parking"** → Properties with parking/garage
- **"garage"** → Properties with garage
- **"view"** → Properties with scenic views
- **"city view"** → Properties with city views

## Configuration

Edit `semantic_config.json` to customize your search:

```json
{
  "search_area": {
    "center": "Mission District, San Francisco, CA",
    "radius_miles": 0.5,
    "auto_bounds": true
  },
  "filters": {
    "min_price": 1200000,
    "max_price": 1750000,
    "min_sqft": 750,
    "max_sqft": 1500,
    "home_types": ["CONDO", "SINGLE_FAMILY", "TOWNHOUSE"],
    "include_sold": false,
    "max_sold_age_months": 6
  },
  "semantic": {
    "enable_semantic_search": true,
    "semantic_weight": 0.3,
    "max_semantic_results": 50,
    "min_semantic_score": 0.3
  },
  "output": {
    "html_file": "semantic_search_results.html",
    "json_file": "semantic_search_data.json",
    "max_listings": 200
  }
}
```

## How It Works

### 1. Query Interpretation
The tool analyzes your natural language query and extracts:
- **Home type preferences** (townhouse, single family, top floor condo)
- **Condition preferences** (good condition, not fixer-upper)
- **Feature preferences** (outdoor space, parking, views)
- **Exclusions** (fixer-upper, noisy areas)

### 2. Hybrid Search
- **Hard filters** are applied to Zillow's API (price, sqft, location)
- **Semantic scoring** ranks properties based on natural language matches
- **Combined ranking** prioritizes properties that match both criteria

### 3. Semantic Scoring
Properties receive scores (0-1) based on:
- Home type matches (0.3 points)
- Floor level preferences (0.4 points for top floor)
- Condition indicators (0.2-0.3 points)
- Feature matches (0.2 points each)

### 4. Results Display
- Properties are ranked by semantic relevance
- Match explanations show why each property scored well
- HTML reports include semantic score and match details

## Command Line Options

```bash
python semantic_house_search.py [OPTIONS]

Options:
  --config PATH          Path to configuration file
  --query TEXT           Semantic search query
  --price RANGE          Price range (e.g., '1.2M-1.75M')
  --sqft RANGE           Square footage range (e.g., '750-1500')
  --center LOCATION      Search center location
  --radius MILES         Search radius in miles
  --create-config        Create sample configuration file
```

## Example Usage

```bash
# Find townhomes or top floor condos, not fixer-uppers, in Mission District
python semantic_house_search.py \
  --query "no one living above me, NOT a fixer-upper" \
  --price "1.2M-1.75M" \
  --sqft "750-1500" \
  --center "Mission District, San Francisco, CA" \
  --radius 0.5

# Find properties with outdoor space and parking
python semantic_house_search.py \
  --query "outdoor space, parking" \
  --price "1M-2M" \
  --sqft "1000-2000"

# Find quiet, move-in ready properties
python semantic_house_search.py \
  --query "quiet, move-in ready" \
  --price "1.5M-2.5M"
```

## Output Files

- **`semantic_search_results.html`**: Beautiful HTML report with semantic match explanations
- **`semantic_search_data.json`**: Structured data including semantic scores and matches

## Supported Locations

The tool recognizes common SF neighborhood names:
- Mission District / Mission
- SOMA / South of Market
- Financial District
- Castro
- Noe Valley
- Bernal Heights
- Potrero Hill
- Hayes Valley
- Marina
- Russian Hill
- North Beach
- Pacific Heights
- Sunset
- Richmond
- And more...

## Technical Details

### Semantic Mapping
The tool uses a comprehensive mapping system to translate natural language to property characteristics:

```python
semantic_mappings = {
    "no one living above": {
        "home_types": ["TOWNHOUSE", "SINGLE_FAMILY"],
        "preferences": ["top_floor_condo"],
        "excluded_home_types": ["mid_floor_condo", "ground_floor_condo"]
    },
    "not a fixer-upper": {
        "condition_preferences": ["good_condition", "recently_renovated"],
        "exclusions": ["needs_work", "fixer_upper", "handyman_special"]
    }
    # ... more mappings
}
```

### Scoring Algorithm
Properties are scored based on multiple factors:
1. **Home type match** (0.3 points)
2. **Floor level preference** (0.4 points for top floor)
3. **Condition indicators** (0.2-0.3 points)
4. **Feature matches** (0.2 points each)

### Integration with Zillow API
- Uses existing Zillow API infrastructure
- Applies hard filters through Zillow's native filtering
- Enhances results with semantic scoring and ranking
- Maintains compatibility with existing market scanner tools

## Future Enhancements

- **LLM Integration**: Use actual LLM APIs for more sophisticated query interpretation
- **Property Embeddings**: Create vector embeddings for more accurate semantic matching
- **Machine Learning**: Train models on user preferences and feedback
- **Advanced Filters**: Support for more complex property characteristics
- **Real-time Updates**: Live property data updates
- **User Profiles**: Save and reuse search preferences

## Troubleshooting

### Common Issues

1. **No properties found**: Try expanding price range or radius
2. **Low semantic scores**: Adjust `min_semantic_score` in config
3. **API errors**: Check internet connection and Zillow availability

### Debug Mode
Add `--debug` flag to see detailed semantic interpretation:

```bash
python semantic_house_search.py --query "no one living above me" --debug
```

## Contributing

This tool is part of the broader property search ecosystem. To contribute:
1. Add new semantic mappings in `interpret_semantic_query()`
2. Enhance scoring algorithms in `calculate_semantic_score()`
3. Improve HTML report templates
4. Add new property data sources

## License

Part of the price_per_sqft project. See main project README for license information.
