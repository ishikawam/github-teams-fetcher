#!/usr/bin/env python3
"""
Tests for config_loader module
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from github_teams.config_loader import ConfigLoader, get_config


def test_config_loader_with_valid_config():
    """Test ConfigLoader with valid configuration."""
    config_content = """
github:
  organizations:
    - example-org
    - test-org

api:
  max_retries: 3
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigLoader(config_path)

        # Test organization list
        orgs = config.get_organizations()
        assert len(orgs) == 2
        assert "example-org" in orgs
        assert "test-org" in orgs

        # Test API settings
        assert hasattr(config, "config")

    finally:
        Path(config_path).unlink()


def test_config_loader_with_minimal_config():
    """Test ConfigLoader with minimal configuration."""
    config_content = """
github:
  organizations:
    - single-org
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigLoader(config_path)

        # Test organization list
        orgs = config.get_organizations()
        assert len(orgs) == 1
        assert "single-org" in orgs

        # Test basic functionality
        assert hasattr(config, "config")

    finally:
        Path(config_path).unlink()


def test_config_loader_missing_file():
    """Test ConfigLoader with missing configuration file."""
    with pytest.raises(SystemExit):
        ConfigLoader("/nonexistent/path/config.yaml")


def test_get_config_function():
    """Test the get_config() convenience function."""
    # This test assumes config.yaml exists in the project root
    # In actual usage, this would be mocked or use a test config
    try:
        config = get_config()
        assert isinstance(config, ConfigLoader)
        orgs = config.get_organizations()
        assert isinstance(orgs, list)
        assert len(orgs) > 0
    except FileNotFoundError:
        # If config.yaml doesn't exist, that's expected in test environment
        pytest.skip("config.yaml not found - expected in test environment")
