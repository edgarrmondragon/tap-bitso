"""Bitso tap class."""

from typing import List

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_bitso.streams import (
    BooksStream,
    LedgerStream,
    TickersStream,
    TradesStream,
    UserTradesStream,
)

STREAM_TYPES = [
    BooksStream,
    LedgerStream,
    TickersStream,
    UserTradesStream,
    TradesStream,
]


class TapBitso(Tap):
    """Bitso tap class."""

    name = "tap-bitso"

    config_jsonschema = th.PropertiesList(
        th.Property("key", th.StringType, required=True),
        th.Property("secret", th.StringType, required=True),
        th.Property("base_url", th.StringType, default="https://api.bitso.com"),
        th.Property("books", th.ArrayType(th.StringType), default=["btc_mxn"]),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
