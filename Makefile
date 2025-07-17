# Cafe Shams News Bot - Makefile

.PHONY: install run test clean deploy help

# Default target
help:
	@echo "Cafe Shams News Bot - Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run the bot locally"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean cache files"
	@echo "  deploy     - Deploy to Railway"
	@echo "  help       - Show this help message"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

# Run locally
run:
	@echo "Starting Cafe Shams News Bot..."
	python main.py

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

# Clean cache and temporary files
clean:
	@echo "Cleaning cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f sent_urls.json sent_hashes.json bad_links.json

# Deploy to Railway
deploy:
	@echo "Deploying to Railway..."
	git add .
	git commit -m "Deploy: $(shell date)"
	git push origin main

# Setup development environment
dev-setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env file with your bot token and chat IDs"

# Check code style
lint:
	@echo "Checking code style..."
	flake8 main.py --max-line-length=120

# Show bot status
status:
	@echo "Checking bot status..."
	curl -s https://your-app.railway.app/health | jq
