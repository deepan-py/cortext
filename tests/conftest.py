"""Test fixtures for Cortex."""

import pytest
from pathlib import Path


@pytest.fixture
def timeline_dir(tmp_path: Path) -> Path:
    """Create a temporary timeline directory."""
    tl = tmp_path / "timeline"
    tl.mkdir()
    return tl


@pytest.fixture
def valid_yaml() -> str:
    """Minimal valid decision record YAML."""
    return """\
id: "2025-04-25-001"
status: active
date: "2025-04-25"
author: human
domains:
  - auth
decision: "Use JWT with RS256 for API auth."
context: "Need stateless auth across multiple service instances."
"""
