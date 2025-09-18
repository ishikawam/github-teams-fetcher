"""
GitHub Teams Fetcher

A tool for fetching and analyzing GitHub organization team and member data.
"""

__version__ = "1.0.0"

from .config_loader import get_config
from .metadata_manager import MetadataManager
from .smart_fetcher import SmartFetcher

__all__ = ["get_config", "MetadataManager", "SmartFetcher"]
