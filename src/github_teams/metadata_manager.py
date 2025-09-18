#!/usr/bin/env python3
"""
Metadata Manager for Incremental Updates

Manages update timestamps, checksums, and API usage tracking
for efficient differential updates of GitHub organization data.
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class MetadataManager:
    """Manages metadata for incremental updates."""

    def __init__(self, base_dir: str = "data", organization: str = None):
        from config_loader import get_config

        if organization:
            config = get_config()
            self.base_dir = Path(config.get_data_directory(organization))
        else:
            self.base_dir = Path(base_dir)

        self.metadata_dir = self.base_dir / "metadata"
        self.cache_dir = self.base_dir / "cache"

        # Ensure directories exist
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.update_file = self.metadata_dir / "last_update.yaml"
        self.checksum_file = self.metadata_dir / "checksums.yaml"
        self.api_usage_file = self.metadata_dir / "api_usage.yaml"

    def load_metadata(self) -> Dict[str, Any]:
        """Load all metadata from files."""
        metadata = {
            "last_update": self._load_yaml(self.update_file, {}),
            "checksums": self._load_yaml(self.checksum_file, {}),
            "api_usage": self._load_yaml(self.api_usage_file, {}),
        }
        return metadata

    def _load_yaml(self, file_path: Path, default: Any) -> Any:
        """Load YAML file with default fallback."""
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or default
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        return default

    def _save_yaml(self, file_path: Path, data: Any) -> None:
        """Save data to YAML file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Error: Could not save {file_path}: {e}")

    def update_timestamp(self, resource_type: str) -> None:
        """Update last update timestamp for a resource type."""
        current_data = self._load_yaml(self.update_file, {})
        current_data[resource_type] = datetime.now().isoformat()
        self._save_yaml(self.update_file, current_data)

    def get_last_update(self, resource_type: str) -> Optional[datetime]:
        """Get last update timestamp for a resource type."""
        data = self._load_yaml(self.update_file, {})
        timestamp_str = data.get(resource_type)
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                return None
        return None

    def needs_update(self, resource_type: str, threshold_minutes: int = 60) -> bool:
        """Check if a resource type needs update based on threshold."""
        last_update = self.get_last_update(resource_type)
        if not last_update:
            return True

        time_diff = datetime.now() - last_update
        return time_diff > timedelta(minutes=threshold_minutes)

    def calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data integrity checking."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()[:16]

    def update_checksum(self, resource_type: str, data: Any) -> None:
        """Update checksum for a resource type."""
        current_data = self._load_yaml(self.checksum_file, {})
        current_data[resource_type] = self.calculate_checksum(data)
        self._save_yaml(self.checksum_file, current_data)

    def get_checksum(self, resource_type: str) -> Optional[str]:
        """Get stored checksum for a resource type."""
        data = self._load_yaml(self.checksum_file, {})
        return data.get(resource_type)

    def has_checksum_changed(self, resource_type: str, current_data: Any) -> bool:
        """Check if data has changed by comparing checksums."""
        stored_checksum = self.get_checksum(resource_type)
        if not stored_checksum:
            return True

        current_checksum = self.calculate_checksum(current_data)
        return stored_checksum != current_checksum

    def track_api_call(self, endpoint: str) -> None:
        """Track API call for rate limiting monitoring."""
        current_data = self._load_yaml(self.api_usage_file, {})
        today = datetime.now().date().isoformat()

        if "daily_usage" not in current_data:
            current_data["daily_usage"] = {}

        if today not in current_data["daily_usage"]:
            current_data["daily_usage"][today] = {}

        if endpoint not in current_data["daily_usage"][today]:
            current_data["daily_usage"][today][endpoint] = 0

        current_data["daily_usage"][today][endpoint] += 1
        current_data["last_call"] = datetime.now().isoformat()

        self._save_yaml(self.api_usage_file, current_data)

    def get_daily_api_usage(self, date: str = None) -> Dict[str, int]:
        """Get API usage for a specific date (default: today)."""
        if not date:
            date = datetime.now().date().isoformat()

        data = self._load_yaml(self.api_usage_file, {})
        return data.get("daily_usage", {}).get(date, {})

    def get_total_daily_calls(self, date: str = None) -> int:
        """Get total API calls for a date."""
        usage = self.get_daily_api_usage(date)
        return sum(usage.values())

    def save_cache(self, cache_key: str, data: Any, etag: str = None) -> None:
        """Save data to cache with optional ETag."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_data = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "etag": etag,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save cache {cache_key}: {e}")

    def load_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load data from cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache {cache_key}: {e}")
        return None

    def get_cache_etag(self, cache_key: str) -> Optional[str]:
        """Get ETag from cached data."""
        cache_data = self.load_cache(cache_key)
        return cache_data.get("etag") if cache_data else None

    def is_cache_valid(self, cache_key: str, max_age_minutes: int = 60) -> bool:
        """Check if cached data is still valid."""
        cache_data = self.load_cache(cache_key)
        if not cache_data:
            return False

        try:
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - cache_time
            return age < timedelta(minutes=max_age_minutes)
        except (KeyError, ValueError):
            return False

    def cleanup_old_cache(self, max_age_days: int = 7) -> None:
        """Remove old cache files."""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if cache_file.stat().st_mtime < cutoff_time.timestamp():
                    cache_file.unlink()
                    print(f"Removed old cache file: {cache_file.name}")
            except Exception as e:
                print(f"Warning: Could not remove cache file {cache_file}: {e}")

    def get_status_report(self) -> Dict[str, Any]:
        """Generate status report of metadata and cache."""
        metadata = self.load_metadata()

        # Calculate cache statistics
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_size = sum(f.stat().st_size for f in cache_files if f.exists())

        # Get today's API usage
        daily_usage = self.get_daily_api_usage()
        total_calls = sum(daily_usage.values())

        return {
            "last_updates": metadata["last_update"],
            "checksums": {k: v[:8] + "..." for k, v in metadata["checksums"].items()},
            "cache": {
                "files_count": len(cache_files),
                "total_size_kb": cache_size // 1024,
            },
            "api_usage": {
                "today_total": total_calls,
                "today_by_endpoint": daily_usage,
                "rate_limit_remaining": 5000 - total_calls,  # GitHub API limit
            },
        }


if __name__ == "__main__":
    # Example usage and testing
    manager = MetadataManager()

    # Test basic functionality
    print("Testing MetadataManager...")

    # Test timestamp updates
    manager.update_timestamp("teams")
    last_update = manager.get_last_update("teams")
    print(f"Last teams update: {last_update}")

    # Test checksum functionality
    test_data = [{"name": "team1"}, {"name": "team2"}]
    manager.update_checksum("teams", test_data)
    print(f"Teams changed: {manager.has_checksum_changed('teams', test_data)}")

    # Test cache functionality
    manager.save_cache("teams_list", test_data, "etag123")
    cached_data = manager.load_cache("teams_list")
    print(f"Cache loaded successfully: {cached_data is not None}")

    # Generate status report
    status = manager.get_status_report()
    print("\nStatus Report:")
    print(yaml.dump(status, default_flow_style=False))
