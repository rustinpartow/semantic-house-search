#!/usr/bin/env python3
"""test_app.py
Simple test script to verify the application works
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from semantic_house_search import SemanticHouseSearch, load_config
        print("✅ semantic_house_search module imported successfully")
        
        from app import app
        print("✅ Flask app imported successfully")
        
        import requests
        print("✅ requests module available")
        
        import flask
        print("✅ Flask module available")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_semantic_search():
    """Test basic semantic search functionality"""
    try:
        from semantic_house_search import SemanticHouseSearch, DEFAULT_CONFIG
        
        # Create a simple config
        config = DEFAULT_CONFIG.copy()
        config["search_area"]["center"] = "San Francisco, CA"
        config["search_area"]["radius_miles"] = 0.5
        config["filters"]["min_price"] = 1000000
        config["filters"]["max_price"] = 2000000
        
        # Create searcher
        searcher = SemanticHouseSearch(config)
        print("✅ SemanticHouseSearch instance created")
        
        # Test query interpretation
        interpreted = searcher.interpret_semantic_query("no one living above me")
        print(f"✅ Query interpretation works: {len(interpreted)} filter categories")
        
        return True
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    try:
        from app import app
        
        # Test app creation
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint works")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test main page
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main page loads")
            else:
                print(f"❌ Main page failed: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Semantic House Search Application")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Semantic Search Test", test_semantic_search),
        ("Flask App Test", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the application:")
        print("   python app.py")
        print("\n🌐 Then open: http://localhost:5000")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
