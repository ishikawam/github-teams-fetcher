.PHONY: help install setup clean test lint fix fetch matrix report config-check

# Configuration variables (will be dynamically determined by Python scripts)

# Default target
help:
	@echo "GitHub Teams Fetcher v1.0.0"
	@echo "=============================================="
	@echo ""
	@echo "🚀 Main Commands:"
	@echo "  make setup        - Create config.yaml from template"
	@echo "  make install      - Install Python dependencies"
	@echo "  make fetch        - Smart fetch all team and member data (with caching)"
	@echo "  make reports      - Generate reports with differential updates"
	@echo ""
	@echo "🛠️  Development Commands:"
	@echo "  make test         - Run comprehensive test suite"
	@echo "  make lint         - Run code quality checks (flake8, black, isort)"
	@echo "  make fix          - Auto-fix code formatting issues"
	@echo "  make clean        - Clean cache (preserve reports in storage/reports/)"
	@echo ""
	@echo "🔧 Utility Commands:"
	@echo "  make config-check - Validate configuration and dependencies"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "📖 Quick Start:"
	@echo "  1. make setup && make install"
	@echo "  2. gh auth login"
	@echo "  3. Edit config.yaml with your organization names"
	@echo "  4. make fetch && make reports"
	@echo ""
	@echo "📚 Documentation: https://github.com/ishikawam/github-teams-fetcher#readme"

# Install dependencies
install: venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

venv:
	python3 -m venv venv

# Setup configuration
setup:
	@echo "Creating configuration file..."
	@if [ ! -f config.yaml ]; then \
		cp config.yaml.example config.yaml; \
		echo "config.yaml created from template."; \
		echo ""; \
		echo "Please follow these steps:"; \
		echo "1. Edit config.yaml to set your organization names"; \
		echo "2. Authenticate with GitHub CLI: gh auth login"; \
		echo "3. Fetch data: make fetch"; \
	else \
		echo "config.yaml already exists."; \
	fi

# Check configuration and dependencies
config-check: venv
	@echo "Checking configuration and dependencies..."
	@which gh > /dev/null || (echo "Error: GitHub CLI (gh) required. Install: brew install gh" && exit 1)
	@which jq > /dev/null || (echo "Error: jq required. Install: brew install jq" && exit 1)
	@. venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from github_teams.config_loader import get_config; get_config()" > /dev/null
	@echo "Configuration OK"

# Fetch all data (with smart caching)
fetch: config-check
	@echo "Fetching data for all configured organizations..."
	@. venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from github_teams.smart_fetcher import SmartFetcher, MultiOrgFetcher; from github_teams.config_loader import get_config; config = get_config(); orgs = config.get_organizations(); (MultiOrgFetcher().fetch_all_organizations() if len(orgs) > 1 else SmartFetcher().fetch_all())"

# Generate matrix CSV and summary report efficiently
reports: fetch
	@echo "Generating member×team matrix and summary report for all organizations..."
	@. venv/bin/activate && python scripts/generate_batch_reports.py

# Development commands
test: venv
	. venv/bin/activate && python -m pytest tests/ -v -o cache_dir=storage/.pytest_cache

lint: venv
	. venv/bin/activate && flake8 . --exclude=venv --count --select=E9,F63,F7,F82 --show-source --statistics
	. venv/bin/activate && flake8 . --exclude=venv --count --exit-zero --max-line-length=150 --ignore=C901,W503,E226 --statistics
	. venv/bin/activate && black --check --diff . --exclude=venv --line-length=150
	. venv/bin/activate && isort --check-only --diff . --skip=venv --line-length=150 --profile=black

fix: venv
	. venv/bin/activate && black . --exclude=venv --line-length=150
	. venv/bin/activate && isort . --skip=venv --line-length=150 --profile=black

# Clean orphaned files from deleted teams
clean-orphaned: config-check
	@echo "Cleaning orphaned files from deleted teams..."
	@. venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from github_teams.smart_fetcher import SmartFetcher; SmartFetcher().clean_orphaned_files()"

# Clean cache only (preserves important reports and venv)
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf storage/cache/
	rm -rf storage/.pytest_cache/
	@echo "Cache cleaned (reports in storage/reports/ and venv/ preserved)"
