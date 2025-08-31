# 🚀 Deployment Guide

This guide will help you deploy the Semantic House Search application to Cloudflare Pages.

## 📋 Prerequisites

- Cloudflare account
- GitHub repository with the code
- Domain name (optional, Cloudflare provides a free subdomain)

## 🌐 Cloudflare Pages Deployment

### Step 1: Prepare Your Repository

1. **Create a new GitHub repository** for the semantic house search project
2. **Push your code** to the repository
3. **Ensure all files are included**:
   - `app.py` (Flask application)
   - `semantic_house_search.py` (Core search engine)
   - `requirements.txt` (Dependencies)
   - `templates/` directory (HTML templates)
   - `static/` directory (CSS, JS, images)
   - `README.md` (Documentation)

### Step 2: Connect to Cloudflare Pages

1. **Log in to Cloudflare Dashboard**
2. **Go to Pages** in the left sidebar
3. **Click "Create a project"**
4. **Connect to Git** and select your GitHub repository
5. **Choose the repository** containing your semantic house search code

### Step 3: Configure Build Settings

**Framework preset**: None (or Custom)

**Build settings**:
- **Build command**: `pip install -r requirements.txt`
- **Build output directory**: `.`
- **Root directory**: `/` (or leave empty)

**Environment variables**:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: `your-secret-key-here` (generate a random string)
- `PYTHON_VERSION`: `3.9`

### Step 4: Deploy

1. **Click "Save and Deploy"**
2. **Wait for the build** to complete (usually 2-5 minutes)
3. **Your app will be available** at `https://your-project-name.pages.dev`

### Step 5: Custom Domain (Optional)

1. **Go to your Pages project**
2. **Click "Custom domains"**
3. **Add your domain** (e.g., `semantic-house-search.yourdomain.com`)
4. **Follow DNS setup instructions**

## 🔧 Configuration

### Environment Variables

Set these in your Cloudflare Pages project settings:

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
PYTHON_VERSION=3.9
```

### Build Configuration

The application uses a simple build process:

1. **Install Python dependencies** from `requirements.txt`
2. **Start the Flask application** with `app.py`
3. **Serve static files** from the `static/` directory

## 🧪 Testing Your Deployment

### 1. Health Check
Visit: `https://your-app.pages.dev/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2023-08-30T16:00:00"
}
```

### 2. Main Application
Visit: `https://your-app.pages.dev/`

You should see the semantic house search interface.

### 3. API Test
Test the search API:

```bash
curl -X POST https://your-app.pages.dev/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "no one living above me, NOT a fixer-upper",
    "min_price": 1000000,
    "max_price": 2000000,
    "min_sqft": 1000,
    "max_sqft": 2000,
    "center": "San Francisco, CA",
    "radius": 2.0
  }'
```

## 🔍 Troubleshooting

### Common Issues

1. **Build Fails**
   - Check that `requirements.txt` is in the root directory
   - Verify Python version is set to 3.9
   - Check build logs for specific error messages

2. **App Doesn't Start**
   - Verify `app.py` is in the root directory
   - Check that all dependencies are installed
   - Review environment variables

3. **404 Errors from Zillow**
   - The app includes rate limiting to avoid being blocked
   - This is normal behavior - the app will retry with fallback methods

4. **Slow Performance**
   - Searches may take 10-30 seconds due to rate limiting
   - This is intentional to avoid being blocked by Zillow

### Debug Mode

For development, you can run locally:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py
```

## 📊 Monitoring

### Cloudflare Analytics

Cloudflare Pages provides built-in analytics:
- Page views
- Unique visitors
- Performance metrics
- Error rates

### Application Logs

Check the Cloudflare Pages dashboard for:
- Build logs
- Runtime logs
- Error messages

## 🔒 Security Considerations

### Rate Limiting

The application includes built-in rate limiting to:
- Avoid being blocked by Zillow
- Prevent abuse
- Ensure fair usage

### API Security

- No authentication required (public search tool)
- Rate limiting prevents abuse
- Error handling prevents information leakage

## 🚀 Scaling

### Performance Optimization

- **Caching**: Consider adding Redis for result caching
- **CDN**: Cloudflare provides global CDN automatically
- **Database**: For production, consider adding a database for user preferences

### Cost Optimization

- **Cloudflare Pages**: Free tier includes 500 builds/month
- **Bandwidth**: Free tier includes 20GB/month
- **Custom domains**: Free with Cloudflare

## 📈 Future Enhancements

### Production Features

1. **User Authentication**: Add user accounts and saved searches
2. **Database Integration**: Store user preferences and search history
3. **Caching Layer**: Redis for faster repeated searches
4. **Monitoring**: Add application performance monitoring
5. **Analytics**: Track search patterns and popular queries

### Deployment Options

- **Docker**: Containerize for easier deployment
- **Kubernetes**: For high-scale deployments
- **Multi-region**: Deploy to multiple Cloudflare regions

## 📞 Support

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Cloudflare Support**: For deployment issues
- **Documentation**: Check the main README.md

### Contributing

- Fork the repository
- Create a feature branch
- Submit a pull request
- Follow the contribution guidelines

---

**Happy Deploying! 🎉**
