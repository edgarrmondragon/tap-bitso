"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

from typing import Any

import pytest
import stamina
from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_bitso.tap import TapBitso

SAMPLE_CONFIG: dict[str, Any] = {}


@pytest.fixture(autouse=True, scope="session")
def _deactivate_retries() -> None:
    """Deactivate stamina retries for all tests."""
    stamina.set_active(active=False)


TestTapBitso = get_tap_test_class(
    TapBitso,
    config=SAMPLE_CONFIG,
    suite_config=SuiteConfig(
        ignore_no_records_for_streams=["user_trades"],
        max_records_limit=50,
    ),
)
