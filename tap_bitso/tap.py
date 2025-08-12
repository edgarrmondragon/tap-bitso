"""Bitso tap class."""

from __future__ import annotations

import sys

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_bitso import streams

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class TapBitso(Tap):
    """Bitso tap class."""

    name = "tap-bitso"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "key",
            th.StringType,
            required=True,
            description="Bitso API Key",
        ),
        th.Property(
            "secret",
            th.StringType,
            required=True,
            description="Bitso API Secret",
        ),
        th.Property(
            "base_url",
            th.StringType,
            default="https://api.bitso.com",
            description="Bitso API base URL",
        ),
        th.Property(
            "books",
            th.ArrayType(th.StringType),
            default=["btc_mxn"],
            description=(
                "Specifies which book to use for `tickers` and other endpoints"
            ),
        ),
    ).to_dict()

    @override
    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams.

        Returns:
            A list of streams.
        """
        return [
            streams.BooksStream(tap=self),
            # streams.LedgerStream(tap=self),  # Removed upstream?  # noqa: ERA001
            streams.TickersStream(tap=self),
            streams.TradesStream(tap=self),
            streams.UserTradesStream(tap=self),
        ]
