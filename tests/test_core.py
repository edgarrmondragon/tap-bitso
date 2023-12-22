"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

from typing import Any

from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_bitso.tap import TapBitso

SAMPLE_CONFIG: dict[str, Any] = {}


TestTapBitso = get_tap_test_class(
    TapBitso,
    config=SAMPLE_CONFIG,
    suite_config=SuiteConfig(
        ignore_no_records_for_streams=["user_trades"],
        max_records_limit=50,
    ),
)
