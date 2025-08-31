# 🧠 Semantic House Search

A powerful web application that combines Zillow's property data with AI-powered semantic search capabilities. Find your perfect home using natural language queries like "no one living above me, NOT a fixer-upper, high ceilings, natural light."

## ✨ Features

### 🧠 Natural Language Search
- **Semantic Query Interpretation**: Understands complex, nuanced property preferences
- **Smart Filtering**: Maps natural language to specific property characteristics
- **Neighborhood Intelligence**: Recognizes preferred and avoided areas
- **Architectural Preferences**: Detects modern vs. old architecture preferences

### 🏠 Property Analysis
- **Hybrid Ranking**: Combines hard filters with semantic relevance scoring
- **Detailed Explanations**: Shows exactly why each property matches your criteria
- **Comprehensive Data**: Price, size, location, condition, and semantic scores
- **Beautiful Reports**: Modern, responsive web interface

### 🌐 Web Application
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Real-time Search**: Fast, interactive property search
- **API Endpoints**: RESTful API for programmatic access
- **Error Handling**: Robust error handling and user feedback

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd semantic-house-search
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

### Example Queries

Try these natural language queries:

- **"no one living above me, NOT a fixer-upper"**
- **"high ceilings, natural light, modern kitchen"**
- **"quiet neighborhood, outdoor space, parking"**
- **"move-in ready, city view, not too residential"**
- **"not edwardian, not super old, safe area like Cole Valley"**

## 🏗️ Architecture

### Backend (Flask)
- **`app.py`**: Main Flask application with API endpoints
- **`semantic_house_search.py`**: Core semantic search engine
- **API Endpoints**:
  - `POST /api/search`: Main search endpoint
  - `GET /api/neighborhoods`: Supported neighborhoods
  - `GET /health`: Health check

### Frontend (HTML/CSS/JavaScript)
- **`templates/index.html`**: Main search interface
- **`static/css/style.css`**: Beautiful, responsive styling
- **`static/js/app.js`**: Interactive frontend functionality

### Semantic Search Engine
- **Query Interpretation**: Maps natural language to structured filters
- **Property Scoring**: 0-1 semantic relevance scores
- **Hybrid Ranking**: Combines semantic and traditional metrics
- **Zillow Integration**: Fetches real property data

## 🧠 How Semantic Search Works

### 1. Query Interpretation
The system analyzes your natural language query and extracts:

```python
# Example: "no one living above me, NOT a fixer-upper"
interpreted_filters = {
    "home_types": ["SINGLE_FAMILY", "TOWNHOUSE"],
    "preferences": ["top_floor_condo"],
    "exclusions": ["fixer_upper", "needs_work"],
    "condition_preferences": ["good_condition", "recently_renovated"]
}
```

### 2. Property Scoring
Each property receives a semantic score based on:

- **Home type matches** (0.3 points)
- **Floor level preferences** (0.4 points for top floor)
- **Condition indicators** (0.2-0.3 points)
- **Neighborhood preferences** (0.3 points)
- **Feature matches** (0.2 points each)

### 3. Hybrid Ranking
Properties are ranked by:
1. **Semantic relevance score** (primary)
2. **Price per square foot** (secondary)
3. **Traditional metrics** (tertiary)

## 🌐 Deployment

### Cloudflare Pages

1. **Connect your repository** to Cloudflare Pages
2. **Configure build settings**:
   - Build command: `pip install -r requirements.txt`
   - Build output directory: `.`
   - Python version: `3.9`

3. **Set environment variables**:
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: Your secret key

4. **Deploy**: Cloudflare will automatically build and deploy

### Other Platforms

The application can be deployed to any platform that supports Python/Flask:

- **Heroku**: Use the included `requirements.txt`
- **Railway**: Direct deployment from GitHub
- **DigitalOcean App Platform**: Python app deployment
- **AWS Elastic Beanstalk**: Flask application deployment

## 📊 API Documentation

### Search Properties
```http
POST /api/search
Content-Type: application/json

{
  "query": "no one living above me, NOT a fixer-upper",
  "min_price": 1000000,
  "max_price": 2000000,
  "min_sqft": 1000,
  "max_sqft": 2000,
  "center": "San Francisco, CA",
  "radius": 2.0
}
```

**Response:**
```json
{
  "success": true,
  "query": "no one living above me, NOT a fixer-upper",
  "interpreted_filters": { ... },
  "properties": [ ... ],
  "summary": { ... },
  "search_date": "2023-08-30T16:00:00"
}
```

### Get Neighborhoods
```http
GET /api/neighborhoods
```

**Response:**
```json
[
  "Mission District", "SOMA", "Financial District", 
  "Castro", "Noe Valley", "Bernal Heights", ...
]
```

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV`: Set to `development` for debug mode
- `SECRET_KEY`: Flask secret key for sessions
- `PORT`: Port number (default: 5000)

### Search Configuration
Edit `semantic_config.json` to customize:

```json
{
  "search_area": {
    "center": "San Francisco, CA",
    "radius_miles": 2.0
  },
  "filters": {
    "min_price": 1000000,
    "max_price": 2000000,
    "min_sqft": 1000,
    "max_sqft": 2000
  },
  "semantic": {
    "enable_semantic_search": true,
    "min_semantic_score": 0.0
  }
}
```

## 🧪 Testing

### Run Tests
```bash
# Test the semantic search engine
python -c "from semantic_house_search import SemanticHouseSearch; print('✅ Import successful')"

# Test the Flask app
python -c "from app import app; print('✅ Flask app loaded')"
```

### Manual Testing
1. Start the application: `python app.py`
2. Open `http://localhost:5000`
3. Try various search queries
4. Check the browser console for any errors

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Test your changes thoroughly
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Zillow**: For providing comprehensive property data
- **Flask**: For the excellent web framework
- **Font Awesome**: For beautiful icons
- **The open source community**: For inspiration and tools

## 🐛 Troubleshooting

### Common Issues

1. **404 Errors from Zillow API**
   - The app includes rate limiting and fallback methods
   - If issues persist, try reducing the search radius

2. **No Properties Found**
   - Try expanding your price range or search radius
   - Check that your location is valid

3. **Slow Search Performance**
   - The app includes rate limiting to avoid being blocked
   - Searches may take 10-30 seconds depending on results

### Getting Help

- **Issues**: Open a GitHub issue with detailed information
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainer for urgent issues

## 🔮 Future Enhancements

- **LLM Integration**: Use actual LLM APIs for more sophisticated query interpretation
- **Property Embeddings**: Create vector embeddings for more accurate semantic matching
- **Machine Learning**: Train models on user preferences and feedback
- **Advanced Filters**: Support for more complex property characteristics
- **Real-time Updates**: Live property data updates
- **User Profiles**: Save and reuse search preferences
- **Mobile App**: Native mobile application
- **Multi-city Support**: Expand beyond San Francisco

---

**Built with ❤️ for finding your perfect home**