import pytest
from singer_sdk.testing import get_standard_tap_pytest_parameters

from tap_bitso.tap import TapBitso

test_params = get_standard_tap_pytest_parameters(
    tap_class=TapBitso,
    tap_config={
        "base_url": "https://api.bitso.com",
        "books": ["btc_mxn", "eth_mxn"],
    },
    include_tap_tests=True,
    include_stream_tests=True,
    include_attribute_tests=True,
)


@pytest.mark.parametrize("test", **test_params)
def test_standard_tap_tests(test):
    """Run standard tap tests from the SDK."""
    test.run_test()
