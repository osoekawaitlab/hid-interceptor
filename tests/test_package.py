"""Test package exports."""

import re

import hid_interceptor


def test_version() -> None:
    """Test that the package version is correctly defined."""
    version = hid_interceptor.__version__
    assert isinstance(version, str)
    # Simple semantic versioning pattern check
    pattern = r"^\d+\.\d+\.\d+?$"
    assert re.match(pattern, version), (
        f"Version '{version}' does not match semantic versioning pattern."
    )
