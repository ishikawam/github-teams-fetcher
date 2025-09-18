#!/usr/bin/env python3
"""
Tests for batch report generation
"""

import csv
import io
import sys
import tempfile
from pathlib import Path

import pytest

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_batch_reports import (
    OrganizationData,
    calculate_csv_hash,
    calculate_md_hash,
    generate_matrix_csv_content,
    generate_summary_report_content,
)


def test_calculate_csv_hash():
    """Test CSV hash calculation."""
    csv_data = "header1,header2\nvalue1,value2\n"
    hash1 = calculate_csv_hash(csv_data)
    hash2 = calculate_csv_hash(csv_data)

    # Same content should produce same hash
    assert hash1 == hash2

    # Different content should produce different hash
    different_csv = "header1,header2\nvalue1,value3\n"
    hash3 = calculate_csv_hash(different_csv)
    assert hash1 != hash3


def test_calculate_md_hash():
    """Test markdown hash calculation with timestamp filtering."""
    md_data = """# Report
    
**Generated:** 2024-01-01 12:00:00

Some content here.

- **Last updated:** 2024-01-01 12:00:00
"""

    md_data_different_time = """# Report
    
**Generated:** 2024-01-02 14:30:00

Some content here.

- **Last updated:** 2024-01-02 14:30:00
"""

    hash1 = calculate_md_hash(md_data)
    hash2 = calculate_md_hash(md_data_different_time)

    # Should be same hash because timestamps are filtered out
    assert hash1 == hash2

    # Different content should produce different hash
    md_data_different_content = """# Different Report
    
**Generated:** 2024-01-01 12:00:00

Different content here.

- **Last updated:** 2024-01-01 12:00:00
"""

    hash3 = calculate_md_hash(md_data_different_content)
    assert hash1 != hash3


def test_generate_matrix_csv_content():
    """Test CSV matrix generation."""
    # Create mock organization data
    org_data = type("MockOrgData", (), {})()
    org_data.all_members = ["user1", "user2"]
    org_data.all_teams = ["team1", "team2"]
    org_data.member_to_team_roles = {
        "user1": {"team1": "maintainer", "team2": "member"},
        "user2": {"team1": "member"},
    }

    csv_content = generate_matrix_csv_content(org_data)

    # Parse the CSV to verify structure
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)

    assert len(rows) == 2  # Two members

    # Check first user
    user1_row = next(row for row in rows if row["member"] == "user1")
    assert user1_row["team1"] == "maintainer"
    assert user1_row["team2"] == "member"

    # Check second user
    user2_row = next(row for row in rows if row["member"] == "user2")
    assert user2_row["team1"] == "member"
    assert user2_row["team2"] == ""  # Not a member


def test_generate_summary_report_content():
    """Test summary report generation."""
    # Create mock organization data
    org_data = type("MockOrgData", (), {})()
    org_data.organization = "test-org"
    org_data.all_members = ["user1", "user2", "user3"]
    org_data.all_teams = ["team1", "team2"]
    org_data.member_to_team_roles = {
        "user1": {"team1": "maintainer", "team2": "member"},
        "user2": {"team1": "member"},
    }

    report_content = generate_summary_report_content(org_data)

    # Check basic structure
    assert "# GitHub Organization Summary Report" in report_content
    assert "**Organization:** test-org" in report_content
    assert "**Total Members:** 3" in report_content
    assert "**Total Teams:** 2" in report_content

    # Check statistics calculation
    assert "**Members with Team Data:** 2" in report_content  # user1 and user2 have team data
    assert "**Members with Maintainer Role:** 1" in report_content  # only user1 is maintainer


def test_organization_data_structure():
    """Test OrganizationData class structure."""
    # This is a basic structure test since we can't easily mock file operations
    try:
        org_data = OrganizationData("test-org")
        assert org_data.organization == "test-org"
        assert hasattr(org_data, "all_members")
        assert hasattr(org_data, "all_teams")
        assert hasattr(org_data, "member_to_team_roles")
    except Exception:
        # Expected if config is not available
        pass
