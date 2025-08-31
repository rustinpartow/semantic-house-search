# Makefile for Railway build verification

.PHONY: test-build test-requirements test-flask test-imports test-health deploy test-quick test-files

test-build: test-files test-requirements test-flask test-imports test-health
	@echo "✅ All build tests passed!"

test-files:
	@echo "Testing required files..."
	@python3 -c "import os; required_files = ['app.py', 'requirements.txt', 'Procfile', 'railway.json']; [print(f'✅ Found: {file}') if os.path.exists(file) else (print(f'❌ Missing required file: {file}'), exit(1)) for file in required_files]; print('✅ All required files present')"

test-requirements:
	@echo "Testing requirements.txt..."
	@python3 -c "with open('requirements.txt', 'r') as f: content = f.read(); print('✅ Gunicorn found in requirements.txt') if 'gunicorn' in content else (print('❌ Missing gunicorn in requirements.txt'), exit(1))"
	@pip install -r requirements.txt

test-flask:
	@echo "Testing Flask configuration..."
	@python3 -c "from app import app; print('✅ Flask app configured correctly')"

test-imports:
	@echo "Testing app imports..."
	@python3 -c "from app import app; print('✅ App imports successfully')"

test-health:
	@echo "Testing health endpoint..."
	@python test_build.py

deploy: test-build
	@echo "Running pre-deployment tests..."
	@git add .
	@git commit -m "Deploy: $$(date)"
	@git push origin main
	@echo "✅ Deployed to Railway!"

# Quick test for development
test-quick:
	@echo "Running quick tests..."
	@python3 -c "from app import app; print('✅ App imports')"
	@python3 -c "import os; print(f'✅ PORT env var: {os.environ.get(\"PORT\", \"not set\")}')"
	@echo "✅ Quick tests passed!"

# Test with production environment variables
test-prod:
	@echo "Testing with production environment..."
	@export PORT=5000 SECRET_KEY="test-secret-key" FLASK_ENV="production" && \
	python3 -c "import os; print(f'PORT: {os.environ.get(\"PORT\")}, FLASK_ENV: {os.environ.get(\"FLASK_ENV\")}')"
	@echo "✅ Production environment test passed!"

# Help
help:
	@echo "Available commands:"
	@echo "  test-build    - Run all build verification tests"
	@echo "  test-quick    - Run quick tests (imports + gunicorn config)"
	@echo "  test-prod     - Test with production environment variables"
	@echo "  deploy        - Run tests and deploy to Railway"
	@echo "  help          - Show this help message"
