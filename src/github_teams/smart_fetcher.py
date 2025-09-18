#!/usr/bin/env python3
"""
Smart GitHub teams fetcher with caching support.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from .config_loader import get_config


class SmartFetcher:
    """Smart teams fetcher with file-based caching."""

    def __init__(
        self,
        organization: str = None,
        force_refresh: bool = False,
        cache_hours: int = 24,
    ):
        """Initialize the fetcher.

        Args:
            organization: Organization name (uses first if not specified)
            force_refresh: If True, ignore cache and refresh all data
            cache_hours: Cache duration in hours
        """
        self.config = get_config()
        self.org = organization or self.config.get_organization()
        self.max_retries = self.config.get_max_retries()
        self.force_refresh = force_refresh
        self.cache_hours = cache_hours

    def is_file_fresh(self, file_path: str, max_age_hours: int = None) -> bool:
        """Check if a file is fresh enough to use from cache.

        Args:
            file_path: Path to the file to check
            max_age_hours: Max age in hours (uses instance cache_hours if None)

        Returns:
            True if file exists and is fresh enough
        """
        # If force refresh is enabled, always return False to bypass cache
        if self.force_refresh:
            return False

        if not os.path.exists(file_path):
            return False

        # Use instance cache_hours if not specified
        if max_age_hours is None:
            max_age_hours = self.cache_hours

        file_age = os.path.getmtime(file_path)
        import time

        current_time = time.time()
        age_hours = (current_time - file_age) / 3600

        return age_hours < max_age_hours

    def run_gh_command(self, command: List[str], max_retries: int = None) -> Optional[str]:
        """Run GitHub CLI command with error handling and retry logic.

        Args:
            command: Command to run as list
            max_retries: Maximum number of retries (defaults to config value)

        Returns:
            Command output as string, or None if failed after all retries
        """
        if max_retries is None:
            max_retries = self.max_retries

        for attempt in range(max_retries + 1):
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                return result.stdout
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.strip()

                # Check for rate limit
                if "rate limit" in stderr.lower() or "secondary rate limit" in stderr.lower():
                    if attempt < max_retries:
                        wait_time = min(60 * (2**attempt), 300)  # Exponential backoff, max 5 minutes
                        print(f"Rate limit detected. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue

                # Check for temporary network issues
                if "timeout" in stderr.lower() or "connection" in stderr.lower():
                    if attempt < max_retries:
                        wait_time = 5 * (attempt + 1)  # Linear backoff for network issues
                        print(f"Network issue detected. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue

                # For other errors, fail immediately on last attempt
                if attempt == max_retries:
                    print(f"Error running command {' '.join(command)} after {max_retries + 1} attempts: {stderr}")
                    return None
                else:
                    print(f"Command failed (attempt {attempt + 1}/{max_retries + 1}): {stderr}")
                    time.sleep(2)  # Brief pause before retry

        return None

    def _update_member_files(self, team_name: str, members_data: list, member_names: list) -> None:
        """Update member JSON and txt files with data from roles API call to avoid redundant calls."""
        try:
            members_dir = Path(self.config.get_data_directory(self.org, "members"))
            members_dir.mkdir(parents=True, exist_ok=True)
            (members_dir / "json").mkdir(exist_ok=True)
            (members_dir / "txt").mkdir(exist_ok=True)

            member_json = members_dir / "json" / f"{team_name}.json"
            member_txt = members_dir / "txt" / f"{team_name}.txt"

            # Save JSON data
            import json

            with open(member_json, "w", encoding="utf-8") as f:
                json.dump(members_data, f, indent=2)

            # Save txt data (sorted member names)
            if member_names:
                with open(member_txt, "w", encoding="utf-8") as f:
                    for name in sorted(member_names):
                        f.write(f"{name}\n")
            else:
                # Remove txt file if no members
                if member_txt.exists():
                    member_txt.unlink()

        except Exception as e:
            print(f"  Warning: Could not update member files for {team_name}: {e}")

    def fetch_teams(self) -> bool:
        """Fetch team list with caching.

        Returns:
            True if successful
        """
        teams_dir = Path(self.config.get_data_directory(self.org, "teams"))
        teams_dir.mkdir(parents=True, exist_ok=True)

        teams_json = teams_dir / "all_teams.json"
        teams_txt = teams_dir / "team_names.txt"

        # Check if cached data is fresh
        if self.is_file_fresh(str(teams_json)) and self.is_file_fresh(str(teams_txt)):
            print("Using cached team data (fresh)")
            return True

        print(f"Fetching team list for organization: {self.org}")

        # Fetch teams from GitHub API
        output = self.run_gh_command(["gh", "api", f"orgs/{self.org}/teams", "--paginate"])

        if not output:
            print("Failed to fetch teams")
            return False

        # Save JSON data
        with open(teams_json, "w", encoding="utf-8") as f:
            f.write(output)

        # Extract team names
        try:
            teams_data = json.loads(output)
            team_names = [team["name"] for team in teams_data]

            with open(teams_txt, "w", encoding="utf-8") as f:
                for name in sorted(team_names):
                    f.write(f"{name}\n")

            print(f"Fetched {len(team_names)} teams")
            return True
        except json.JSONDecodeError as e:
            print(f"Error parsing team data: {e}")
            return False

    def fetch_team_members(self, team_name: str) -> bool:
        """Fetch members for a specific team with caching.

        Args:
            team_name: Name of the team

        Returns:
            True if successful
        """
        members_dir = Path(self.config.get_data_directory(self.org, "members"))
        members_dir.mkdir(parents=True, exist_ok=True)
        (members_dir / "json").mkdir(exist_ok=True)
        (members_dir / "txt").mkdir(exist_ok=True)

        member_json = members_dir / "json" / f"{team_name}.json"
        member_txt = members_dir / "txt" / f"{team_name}.txt"

        # Check if cached data is fresh
        # For empty teams, txt file doesn't exist, so check only JSON file
        if self.is_file_fresh(str(member_json)):
            if member_txt.exists():
                # Non-empty team: both files should be fresh
                if self.is_file_fresh(str(member_txt)):
                    return True
            else:
                # Empty team: JSON exists but txt doesn't - check if JSON indicates empty team
                try:
                    with open(member_json, "r", encoding="utf-8") as f:
                        members_data = json.loads(f.read())
                        if not members_data:  # Empty array means empty team
                            print(f"Using cached empty team data for: {team_name}")
                            return True
                except Exception:
                    pass

        print(f"Fetching members for team: {team_name}")

        # Fetch team members
        output = self.run_gh_command(["gh", "api", f"orgs/{self.org}/teams/{team_name}/members", "--paginate"])

        if not output:
            print(f"Failed to fetch members for team: {team_name}")
            return False

        # Save JSON data
        with open(member_json, "w", encoding="utf-8") as f:
            f.write(output)

        # Extract member names
        try:
            members_data = json.loads(output)
            if members_data:  # Only create txt file if there are members
                member_names = [member["login"] for member in members_data]

                with open(member_txt, "w", encoding="utf-8") as f:
                    for name in sorted(member_names):
                        f.write(f"{name}\n")

                print(f"  - {len(member_names)} members")
            else:
                print("  - 0 members")
                # Remove txt file if no members
                if member_txt.exists():
                    member_txt.unlink()

            return True
        except json.JSONDecodeError as e:
            print(f"Error parsing member data for {team_name}: {e}")
            return False

    def fetch_team_members_with_roles(self, team_name: str) -> bool:
        """Fetch team members with roles with caching and robust error handling.

        Args:
            team_name: Name of the team

        Returns:
            True if successful
        """
        roles_dir = Path(self.config.get_data_directory(self.org, "members-with-roles"))
        roles_dir.mkdir(parents=True, exist_ok=True)

        roles_csv = roles_dir / f"{team_name}.csv"
        temp_csv = roles_dir / f"{team_name}.csv.tmp"

        # Check if cached data is fresh and complete
        if self.is_file_fresh(str(roles_csv)) and self._validate_roles_file(roles_csv, team_name):
            return True

        # Need team member list first
        member_txt = Path(self.config.get_data_directory(self.org, "members/txt")) / f"{team_name}.txt"
        if not member_txt.exists():
            # No member txt file means empty team - create empty roles CSV as cache
            print(f"No member file for team: {team_name} (empty team)")
            try:
                with open(temp_csv, "w", encoding="utf-8") as f:
                    f.write("team_name,user_login,role\n")
                temp_csv.rename(roles_csv)
                print(f"  Created empty cache file for empty team {team_name}")
                return True
            except Exception as e:
                print(f"  Error creating empty cache file for {team_name}: {e}")
                return False

        print(f"Fetching roles for team: {team_name}")

        # Use optimized bulk API call to get all team members with roles
        # This replaces individual membership API calls for much better performance
        members_output = self.run_gh_command(["gh", "api", f"orgs/{self.org}/teams/{team_name}/members", "--paginate"])

        if not members_output:
            print(f"  Failed to fetch team members for: {team_name}")
            # Create empty CSV file as cache for teams with no access
            try:
                with open(temp_csv, "w", encoding="utf-8") as f:
                    f.write("team_name,user_login,role\n")
                temp_csv.rename(roles_csv)
                print(f"  Created empty cache file for inaccessible team {team_name}")
                return True
            except Exception as e:
                print(f"  Error creating empty cache file for {team_name}: {e}")
                return False

        try:
            members_data = json.loads(members_output)

            if not members_data:
                print(f"  No members found for team: {team_name}")
                # Create empty CSV file as cache for empty teams
                try:
                    with open(temp_csv, "w", encoding="utf-8") as f:
                        f.write("team_name,user_login,role\n")
                    temp_csv.rename(roles_csv)
                    print(f"  Created empty cache file for empty team {team_name}")
                    return True
                except Exception as e:
                    print(f"  Error creating empty cache file for {team_name}: {e}")
                    return False

            print(f"  Processing {len(members_data)} members with bulk API...")

            # Now get maintainers list to identify roles
            maintainers_output = self.run_gh_command(
                [
                    "gh",
                    "api",
                    f"orgs/{self.org}/teams/{team_name}/members",
                    "--paginate",
                    "-f",
                    "role=maintainer",
                ]
            )

            maintainers_set = set()
            if maintainers_output:
                try:
                    maintainers_data = json.loads(maintainers_output)
                    maintainers_set = {m["login"] for m in maintainers_data}
                except json.JSONDecodeError:
                    print(f"  Warning: Could not parse maintainers data for {team_name}")

            # Build role data from bulk API results
            role_data = []
            member_names = []
            for member in members_data:
                user_login = member.get("login", "")
                if not user_login:
                    continue

                # Determine role based on maintainers list
                role = "maintainer" if user_login in maintainers_set else "member"
                role_data.append((team_name, user_login, role))
                member_names.append(user_login)

            # Also update the basic member files to avoid redundant API calls
            self._update_member_files(team_name, members_data, member_names)

            # Write to temporary file first, then atomically rename
            try:
                with open(temp_csv, "w", encoding="utf-8") as f:
                    f.write("team_name,user_login,role\n")
                    for team_name_val, user, role in role_data:
                        f.write(f"{team_name_val},{user},{role}\n")

                # Atomic rename - this ensures we never have a partially written file
                temp_csv.rename(roles_csv)
                print(f"  Successfully processed {len(role_data)} members for team {team_name}")
                return True

            except Exception as e:
                print(f"  Error writing roles file for {team_name}: {e}")
                # Clean up temporary file
                if temp_csv.exists():
                    temp_csv.unlink()
                return False

        except json.JSONDecodeError as e:
            print(f"  Error parsing team members data for {team_name}: {e}")
            return False

        except Exception as e:
            print(f"Error fetching roles for {team_name}: {e}")
            # Clean up temporary file
            if temp_csv.exists():
                temp_csv.unlink()
            return False

    def _validate_roles_file(self, roles_csv: Path, team_name: str) -> bool:
        """Validate that roles file contains expected number of entries.

        Args:
            roles_csv: Path to roles CSV file
            team_name: Name of the team

        Returns:
            True if file appears complete
        """
        if not roles_csv.exists():
            return False

        member_txt = Path(self.config.get_data_directory(self.org, "members/txt")) / f"{team_name}.txt"
        if not member_txt.exists():
            # No member txt file means empty team - roles CSV should only have header
            try:
                with open(roles_csv, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    # Should only have header line for empty teams
                    if len(lines) == 1 and lines[0] == "team_name,user_login,role":
                        return True
                    else:
                        print(f"  Roles file for empty team {team_name} has unexpected content")
                        return False
            except Exception as e:
                print(f"  Error validating roles file for empty team {team_name}: {e}")
                return False

        try:
            # Count expected members
            with open(member_txt, "r", encoding="utf-8") as f:
                expected_count = len([line for line in f if line.strip()])

            # If no members expected, empty CSV file is valid
            if expected_count == 0:
                return True

            # Count actual role entries (excluding header)
            with open(roles_csv, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                actual_count = len(lines) - 1  # Exclude header

                # Check if all entries are access_denied (complete failure cache)
                if actual_count > 0:
                    access_denied_count = sum(1 for line in lines[1:] if line.endswith(",access_denied"))
                    if access_denied_count == actual_count:
                        print(f"  Roles file for {team_name} contains cached access_denied entries - valid cache")
                        return True

            # Allow up to 5% missing entries (API failures are expected)
            if actual_count >= expected_count * 0.95:
                return True
            else:
                print(f"  Roles file for {team_name} appears incomplete: {actual_count}/{expected_count} entries")
                return False

        except Exception as e:
            print(f"  Error validating roles file for {team_name}: {e}")
            return False

    def fetch_organization_members(self) -> bool:
        """Fetch organization members with caching.

        Returns:
            True if successful
        """
        org_dir = Path(self.config.get_data_directory(self.org, "organization"))
        org_dir.mkdir(parents=True, exist_ok=True)

        org_json = org_dir / "all_members.json"
        org_txt = org_dir / "member_names.txt"

        # Check if cached data is fresh
        if self.is_file_fresh(str(org_json)) and self.is_file_fresh(str(org_txt)):
            print("Using cached organization member data (fresh)")
            return True

        print(f"Fetching organization members for: {self.org}")

        # Fetch organization members
        output = self.run_gh_command(["gh", "api", f"orgs/{self.org}/members", "--paginate"])

        if not output:
            print("Failed to fetch organization members")
            return False

        # Save JSON data
        with open(org_json, "w", encoding="utf-8") as f:
            f.write(output)

        # Extract member names
        try:
            members_data = json.loads(output)
            member_names = [member["login"] for member in members_data]

            with open(org_txt, "w", encoding="utf-8") as f:
                for name in sorted(member_names):
                    f.write(f"{name}\n")

            print(f"Fetched {len(member_names)} organization members")
            return True
        except json.JSONDecodeError as e:
            print(f"Error parsing organization member data: {e}")
            return False

    def clean_orphaned_files(self) -> None:
        """Clean up files for teams that no longer exist."""
        teams_file = Path(self.config.get_data_directory(self.org, "teams/team_names.txt"))
        if not teams_file.exists():
            print("No team list found for cleanup")
            return

        # Get current valid teams
        with open(teams_file, "r", encoding="utf-8") as f:
            current_teams = set(line.strip() for line in f if line.strip())

        print(f"Checking for orphaned files (current teams: {len(current_teams)})...")

        orphaned_files = []

        # Check member files
        members_txt_dir = Path(self.config.get_data_directory(self.org, "members/txt"))
        if members_txt_dir.exists():
            for file_path in members_txt_dir.glob("*.txt"):
                team_name = file_path.stem
                if team_name not in current_teams:
                    orphaned_files.append(file_path)

        members_json_dir = Path(self.config.get_data_directory(self.org, "members/json"))
        if members_json_dir.exists():
            for file_path in members_json_dir.glob("*.json"):
                team_name = file_path.stem
                if team_name not in current_teams:
                    orphaned_files.append(file_path)

        # Check role files
        roles_dir = Path(self.config.get_data_directory(self.org, "members-with-roles"))
        if roles_dir.exists():
            for file_path in roles_dir.glob("*.csv"):
                team_name = file_path.stem
                if team_name not in current_teams:
                    orphaned_files.append(file_path)

        if orphaned_files:
            print(f"Found {len(orphaned_files)} orphaned files from deleted teams:")
            for file_path in orphaned_files:
                print(f"  Removing: {file_path}")
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"    Error removing {file_path}: {e}")
            print(f"Cleaned up {len(orphaned_files)} orphaned files")
        else:
            print("No orphaned files found")

    def fetch_all(self) -> bool:
        """Fetch all data with smart caching and cleanup.

        Returns:
            True if successful
        """
        print("Starting smart data fetch...")

        # 1. Fetch teams
        if not self.fetch_teams():
            return False

        # 2. Clean up files from deleted teams
        self.clean_orphaned_files()

        # 3. Fetch organization members
        if not self.fetch_organization_members():
            return False

        # 4. Read team list and fetch members for each team
        teams_file = Path(self.config.get_data_directory(self.org, "teams/team_names.txt"))
        if not teams_file.exists():
            print("No team list found")
            return False

        with open(teams_file, "r", encoding="utf-8") as f:
            teams = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(teams)} teams...")

        for team in teams:
            # Fetch members with roles (this also updates basic member files)
            if not self.fetch_team_members_with_roles(team):
                print(f"Warning: Failed to fetch roles for team: {team}")
                # Fallback to basic member fetch if roles fetch fails
                if not self.fetch_team_members(team):
                    print(f"Warning: Failed to fetch basic members for team: {team}")
                continue

        print("Smart data fetch completed!")
        return True


class MultiOrgFetcher:
    """Multi-organization smart teams fetcher."""

    def __init__(self, force_refresh: bool = False, cache_hours: int = 24):
        """Initialize the multi-org fetcher."""
        self.config = get_config()
        self.organizations = self.config.get_organizations()
        self.force_refresh = force_refresh
        self.cache_hours = cache_hours

    def fetch_all_organizations(self) -> bool:
        """Fetch data for all configured organizations.

        Returns:
            True if all organizations were processed successfully
        """
        print(f"Starting multi-organization data fetch for {len(self.organizations)} organizations...")

        success_count = 0
        for org in self.organizations:
            print(f"\n{'='*60}")
            print(f"Processing organization: {org}")
            print(f"{'='*60}")

            fetcher = SmartFetcher(org, self.force_refresh, self.cache_hours)
            if fetcher.fetch_all():
                success_count += 1
                print(f"✓ Successfully processed organization: {org}")
            else:
                print(f"✗ Failed to process organization: {org}")

        print(f"\n{'='*60}")
        print("Multi-organization fetch completed!")
        print(f"Success: {success_count}/{len(self.organizations)} organizations")
        print(f"{'='*60}")

        return success_count == len(self.organizations)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Teams Fetcher")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh all data, ignoring cache",
    )
    parser.add_argument(
        "--cache-hours",
        type=int,
        default=24,
        help="Cache duration in hours (default: 24)",
    )
    args = parser.parse_args()

    config = get_config()
    organizations = config.get_organizations()

    if args.force_refresh:
        print("🔄 Force refresh mode enabled - ignoring all cache files")
    elif args.cache_hours != 24:
        print(f"⏰ Using custom cache duration: {args.cache_hours} hours")

    if len(organizations) == 1:
        # Single organization mode (backward compatibility)
        fetcher = SmartFetcher(force_refresh=args.force_refresh, cache_hours=args.cache_hours)
        success = fetcher.fetch_all()
    else:
        # Multi-organization mode
        multi_fetcher = MultiOrgFetcher(force_refresh=args.force_refresh, cache_hours=args.cache_hours)
        success = multi_fetcher.fetch_all_organizations()

    if not success:
        print("Data fetch failed!")
        sys.exit(1)

    print("All data fetched successfully!")


if __name__ == "__main__":
    main()
