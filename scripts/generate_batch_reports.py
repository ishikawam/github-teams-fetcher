#!/usr/bin/env python3
"""
Batch Report Generator - Efficient Matrix and Summary Report Generation

Generates both member×team matrix CSV and summary reports efficiently
by loading data once and sharing it between generators.
"""

import csv
import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from github_teams.config_loader import get_config  # noqa: E402


def calculate_csv_hash(csv_data: str) -> str:
    """Calculate SHA256 hash of CSV data."""
    return hashlib.sha256(csv_data.encode("utf-8")).hexdigest()


def calculate_md_hash(md_data: str) -> str:
    """Calculate SHA256 hash of markdown data, excluding timestamp lines."""
    # Remove timestamp lines for hash calculation
    lines = md_data.split("\n")
    filtered_lines = []
    for line in lines:
        if not (line.startswith("**Generated:**") or line.startswith("- **Last updated:**")):
            filtered_lines.append(line)

    filtered_content = "\n".join(filtered_lines)
    return hashlib.sha256(filtered_content.encode("utf-8")).hexdigest()


def save_csv_with_change_detection(output_data: str, base_filename: Path, organization: str) -> bool:
    """Save CSV data with change detection and date suffix."""
    import subprocess

    reports_dir = base_filename.parent
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Save to base file (always)
    with open(base_filename, "w", encoding="utf-8") as f:
        f.write(output_data)

    # Step 2: Find latest timestamped file
    pattern = f"{base_filename.stem}_*.csv"
    existing_files = sorted(reports_dir.glob(pattern), key=lambda x: x.name, reverse=True)

    # Step 3: Compare with latest timestamped file using shell diff
    if existing_files:
        latest_file = existing_files[0]
        try:
            result = subprocess.run(
                ["diff", str(base_filename), str(latest_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:  # Files are identical
                print(f"No changes detected in {base_filename.name}. Base file updated only.")
                return False
        except Exception as e:
            print(f"Warning: Could not compare with latest file {latest_file}: {e}")

    # Step 4: Create new timestamped file (only if content changed)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = reports_dir / f"{base_filename.stem}_{timestamp}.csv"
    with open(new_filename, "w", encoding="utf-8") as f:
        f.write(output_data)

    print(f"Matrix CSV saved: {base_filename} and {new_filename}")
    return True


def save_md_with_change_detection(output_data: str, base_filename: Path, organization: str) -> bool:
    """Save markdown data with change detection and date suffix."""
    import subprocess

    reports_dir = base_filename.parent
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Save to base file (always)
    with open(base_filename, "w", encoding="utf-8") as f:
        f.write(output_data)

    # Step 2: Find latest timestamped file
    pattern = f"{base_filename.stem}_*.md"
    existing_files = sorted(reports_dir.glob(pattern), key=lambda x: x.name, reverse=True)

    # Step 3: Compare with latest timestamped file using shell diff (ignoring timestamp lines)
    if existing_files:
        latest_file = existing_files[0]
        try:
            # Use diff with grep to ignore timestamp lines
            cmd = (
                f"diff <(grep -v '^\\*\\*Generated:\\*\\*\\|^- \\*\\*Last updated:\\*\\*' '{base_filename}') "
                f"<(grep -v '^\\*\\*Generated:\\*\\*\\|^- \\*\\*Last updated:\\*\\*' '{latest_file}')"
            )
            result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:  # Files are identical (ignoring timestamps)
                print(f"No changes detected in {base_filename.name}. Base file updated only.")
                return False
        except Exception as e:
            print(f"Warning: Could not compare with latest file {latest_file}: {e}")

    # Step 4: Create new timestamped file (only if content changed)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = reports_dir / f"{base_filename.stem}_{timestamp}.md"
    with open(new_filename, "w", encoding="utf-8") as f:
        f.write(output_data)

    print(f"Summary report saved: {base_filename} and {new_filename}")
    return True


class OrganizationData:
    """Holds all data for a single organization."""

    def __init__(self, organization: str):
        self.organization = organization
        self.config = get_config()
        self.all_members = []
        self.all_teams = []
        self.member_to_team_roles = {}
        self.teams_data = []
        self.organization_members_data = []

    def load_all_data(self) -> bool:
        """Load all required data for the organization."""
        print(f"Loading data for organization: {self.organization}")

        # Load organization members
        member_file = Path(self.config.get_data_directory(self.organization, "organization/member_names.txt"))
        if not member_file.exists():
            print(f"Error: {member_file} not found. Please run 'make fetch'.")
            return False

        with open(member_file, "r", encoding="utf-8") as f:
            self.all_members = sorted([line.strip() for line in f if line.strip()])

        # Load team names
        team_file = Path(self.config.get_data_directory(self.organization, "teams/team_names.txt"))
        if not team_file.exists():
            print(f"Error: {team_file} not found. Please run 'make fetch'.")
            return False

        with open(team_file, "r", encoding="utf-8") as f:
            self.all_teams = sorted([line.strip() for line in f if line.strip()])

        # Load team memberships with roles
        self._load_team_memberships_with_roles()

        # Load detailed data for summary report
        self._load_detailed_data()

        print(f"Loaded: {len(self.all_members)} members, {len(self.all_teams)} teams")
        return True

    def _load_team_memberships_with_roles(self):
        """Load team member information with roles."""
        members_with_roles_dir = Path(self.config.get_data_directory(self.organization, "members-with-roles"))

        if not members_with_roles_dir.exists():
            print(f"Error: {members_with_roles_dir} not found. Please run 'make fetch'.")
            return

        for team_file in sorted(members_with_roles_dir.glob("*.csv")):
            team_name = team_file.stem
            try:
                with open(team_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        user_login = row.get("user_login", "").strip()
                        role = row.get("role", "unknown").strip()

                        if not user_login:
                            continue

                        if user_login not in self.member_to_team_roles:
                            self.member_to_team_roles[user_login] = {}
                        self.member_to_team_roles[user_login][team_name] = role

            except Exception as e:
                print(f"Warning: Error reading {team_file}: {e}")
                continue

    def _load_detailed_data(self):
        """Load detailed data for summary reports."""
        # Load teams data
        teams_json = Path(self.config.get_data_directory(self.organization, "teams/all_teams.json"))
        if teams_json.exists():
            try:
                with open(teams_json, "r", encoding="utf-8") as f:
                    self.teams_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load teams data: {e}")

        # Load organization members data
        org_json = Path(self.config.get_data_directory(self.organization, "organization/all_members.json"))
        if org_json.exists():
            try:
                with open(org_json, "r", encoding="utf-8") as f:
                    self.organization_members_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load organization members data: {e}")


def generate_matrix_csv_content(org_data: OrganizationData) -> str:
    """Generate member×team membership matrix CSV content."""
    fieldnames = ["member"] + org_data.all_teams

    # Create CSV content as string
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()

    # Data rows
    for member in org_data.all_members:
        row = {"member": member}
        member_team_roles = org_data.member_to_team_roles.get(member, {})

        for team in org_data.all_teams:
            if team in member_team_roles:
                role = member_team_roles[team]
                if role == "maintainer":
                    row[team] = "maintainer"
                elif role == "member":
                    row[team] = "member"
                elif role == "access_denied":
                    row[team] = "?"
                else:
                    row[team] = "?"
            else:
                row[team] = ""

        writer.writerow(row)

    csv_content = csv_buffer.getvalue()
    csv_buffer.close()
    return csv_content


def generate_summary_report_content(org_data: OrganizationData) -> str:
    """Generate summary report markdown content."""
    # Calculate statistics
    total_members = len(org_data.all_members)
    total_teams = len(org_data.all_teams)

    members_with_teams = len([m for m in org_data.member_to_team_roles.keys() if m in org_data.all_members])
    coverage_rate = members_with_teams / total_members if total_members > 0 else 0

    # Team membership statistics
    team_member_counts = {}
    for team in org_data.all_teams:
        count = sum(1 for roles in org_data.member_to_team_roles.values() if team in roles)
        team_member_counts[team] = count

    # Multi-team members
    multi_team_members = [
        (member, team_roles) for member, team_roles in org_data.member_to_team_roles.items() if len(team_roles) > 1 and member in org_data.all_members
    ]

    # Maintainer statistics
    all_maintainers = set()
    for member, team_roles in org_data.member_to_team_roles.items():
        if any(role == "maintainer" for role in team_roles.values()):
            all_maintainers.add(member)

    # Generate markdown content
    report_content = f"""# GitHub Organization Summary Report

**Organization:** {org_data.organization}

## Overview

- **Total Members:** {total_members:,}
- **Total Teams:** {total_teams:,}
- **Members with Team Data:** {members_with_teams:,} ({coverage_rate:.1%})
- **Members in Multiple Teams:** {len(multi_team_members):,}
- **Members with Maintainer Role:** {len(all_maintainers):,}

## Team Statistics

### Team Size Distribution

"""

    # Team size distribution
    if team_member_counts:
        largest_teams = sorted(team_member_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        report_content += "| Team | Members |\n"
        report_content += "|------|--------:|\n"
        for team, count in largest_teams:
            report_content += f"| {team} | {count:,} |\n"

    # Multi-team members
    if multi_team_members:
        report_content += "\n### Members in Multiple Teams (Top 10)\n\n"
        report_content += "| Member | Teams | Maintainer Roles | Member Roles |\n"
        report_content += "|--------|------:|-----------------:|-------------:|\n"

        for member, team_roles in sorted(multi_team_members, key=lambda x: len(x[1]), reverse=True)[:10]:
            maintainer_count = sum(1 for role in team_roles.values() if role == "maintainer")
            member_count = sum(1 for role in team_roles.values() if role == "member")
            report_content += f"| {member} | {len(team_roles)} | {maintainer_count} | {member_count} |\n"

    report_content += f"""

## Data Quality

- **Role Data Coverage:** {coverage_rate:.1%} of organization members have team role data
- **Total Role Entries:** {sum(len(teams) for teams in org_data.member_to_team_roles.values()):,}

---

*Generated by GitHub Teams Fetcher*
"""

    return report_content


def generate_reports_for_organization(organization: str) -> bool:
    """Generate both matrix and summary reports for a single organization."""
    print(f"\n{'='*60}")
    print(f"Generating reports for organization: {organization}")
    print(f"{'='*60}")

    # Load all data once
    org_data = OrganizationData(organization)
    if not org_data.load_all_data():
        return False

    # Generate matrix CSV
    print("\nGenerating member×team matrix...")
    csv_content = generate_matrix_csv_content(org_data)
    base_csv_file = Path("storage/reports") / organization / "member_team_matrix.csv"
    csv_saved = save_csv_with_change_detection(csv_content, base_csv_file, organization)

    if csv_saved:
        print("Legend: maintainer=Maintainer, member=Member, ?=Unknown/Access Denied, blank=Not a member")

    # Generate summary report
    print("\nGenerating summary report...")
    md_content = generate_summary_report_content(org_data)
    base_md_file = Path("storage/reports") / organization / "summary.md"
    save_md_with_change_detection(md_content, base_md_file, organization)

    # Display quick statistics
    print(f"\n=== Quick Statistics for {organization} ===")
    print(f"Organization members: {len(org_data.all_members):,}")
    print(f"Teams: {len(org_data.all_teams):,}")
    print(f"Members with role data: {len(org_data.member_to_team_roles):,}")

    return True


def generate_all_batch_reports():
    """Generate batch reports for all configured organizations."""
    config = get_config()
    organizations = config.get_organizations()

    print(f"Starting batch report generation for {len(organizations)} organization(s)...")

    success_count = 0
    for org in organizations:
        if generate_reports_for_organization(org):
            success_count += 1

    print(f"\n{'='*60}")
    print("Batch report generation completed!")
    print(f"Successfully processed: {success_count}/{len(organizations)} organizations")
    print(f"{'='*60}")

    return success_count == len(organizations)


if __name__ == "__main__":
    try:
        generate_all_batch_reports()
    except KeyboardInterrupt:
        print("\nBatch report generation interrupted by user.")
    except Exception as e:
        print(f"\nError during batch report generation: {e}")
        print("Please check your data files and try running 'make fetch' first.")
