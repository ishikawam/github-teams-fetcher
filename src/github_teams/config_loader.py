#!/usr/bin/env python3
"""
Configuration loader for GitHub Teams Fetcher.
"""

import os
import sys
from typing import Any, Dict, List

import yaml


class ConfigLoader:
    """Configuration loader class."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize the config loader.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        if not os.path.exists(self.config_file):
            print(
                f"Error: Configuration file '{self.config_file}' not found.",
                file=sys.stderr,
            )
            print(
                "Please copy config.yaml.example to config.yaml and configure it.",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Validate required configuration
            github_config = config.get("github", {})

            # Support both single organization (backward compatibility) and multiple organizations
            organization = github_config.get("organization")
            organizations = github_config.get("organizations", [])

            if not organization and not organizations:
                print(
                    "Error: github.organization or github.organizations must be configured.",
                    file=sys.stderr,
                )
                sys.exit(1)

            # If both are specified, prefer organizations
            if organization and not organizations:
                config["github"]["organizations"] = [organization]
            elif not organizations:
                print("Error: github.organizations cannot be empty.", file=sys.stderr)
                sys.exit(1)

            return config
        except yaml.YAMLError as e:
            print(f"Error: Failed to load configuration file: {e}", file=sys.stderr)
            sys.exit(1)

    def get_organizations(self) -> List[str]:
        """Get GitHub organization names.

        Returns:
            List of organization names
        """
        return self.config["github"]["organizations"]

    def get_organization(self) -> str:
        """Get first GitHub organization name (for backward compatibility).

        Returns:
            Organization name
        """
        organizations = self.get_organizations()
        return organizations[0] if organizations else ""

    def get_data_directory(self, organization: str = None, subdir: str = None) -> str:
        """Get data directory path for an organization.

        Args:
            organization: Organization name (uses first organization if not specified)
            subdir: Subdirectory name

        Returns:
            Directory path
        """
        if not organization:
            organization = self.get_organization()

        base_dir = os.path.join("storage", "cache", organization)
        if subdir:
            return os.path.join(base_dir, subdir)
        return base_dir

    def get_max_retries(self) -> int:
        """Get API max retries setting.

        Returns:
            Number of max retries (default: 3)
        """
        return self.config.get("api", {}).get("max_retries", 3)


def get_config() -> ConfigLoader:
    """Get configuration loader instance.

    Returns:
        ConfigLoader instance
    """
    return ConfigLoader()


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_config()
        print(f"Organizations: {config.get_organizations()}")
        print(f"First organization: {config.get_organization()}")
        print(f"Data directory: {config.get_data_directory()}")
        print("Configuration file loaded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
