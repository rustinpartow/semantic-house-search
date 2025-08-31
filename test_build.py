#!/usr/bin/env python3
"""test_build.py - Automated Railway build verification"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def test_requirements():
    """Test that requirements.txt installs without errors"""
    print("Testing requirements.txt installation...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True, check=True)
        print("✓ Requirements install successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Requirements installation failed: {e.stderr}")
        return False

def test_gunicorn_config():
    """Test Gunicorn configuration"""
    print("Testing Gunicorn configuration...")
    try:
        result = subprocess.run([
            'gunicorn', 'app:app', '--check-config'
        ], capture_output=True, text=True, check=True)
        print("✓ Gunicorn configuration is valid")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Gunicorn configuration failed: {e.stderr}")
        return False

def test_app_imports():
    """Test that app imports without errors"""
    print("Testing app imports...")
    try:
        result = subprocess.run([
            sys.executable, '-c', 'from app import app; print("App imports successfully")'
        ], capture_output=True, text=True, check=True)
        print("✓ App imports successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ App import failed: {e.stderr}")
        return False

def test_health_endpoint():
    """Test health endpoint with Flask"""
    print("Testing health endpoint...")
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = '5001'
    env['SECRET_KEY'] = 'test-secret-key'
    env['FLASK_ENV'] = 'production'
    
    # Start Flask app
    proc = subprocess.Popen([
        'python', 'app.py'
    ], env=env)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get('http://localhost:5001/health', timeout=10)
        if response.status_code == 200:
            print("✓ Health endpoint responds correctly")
            return True
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")
        return False
    finally:
        proc.terminate()

def test_required_files():
    """Test that all required files exist"""
    print("Testing required files...")
    required_files = ['app.py', 'requirements.txt', 'Procfile', 'railway.json']
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"✗ Missing required file: {file}")
            return False
        else:
            print(f"✓ Found: {file}")
    
    return True

def test_gunicorn_in_requirements():
    """Test that gunicorn is in requirements.txt"""
    print("Testing gunicorn in requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'gunicorn' in content:
                print("✓ Gunicorn found in requirements.txt")
                return True
            else:
                print("✗ Gunicorn missing from requirements.txt")
                return False
    except FileNotFoundError:
        print("✗ requirements.txt not found")
        return False

def main():
    """Run all build tests"""
    print("🚀 Running Railway build verification tests...\n")
    
    tests = [
        test_required_files,
        test_gunicorn_in_requirements,
        test_requirements,
        test_gunicorn_config,
        test_app_imports,
        test_health_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Ready for Railway deployment.")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
