"""Bitso tap class."""

from __future__ import annotations

import structlog
from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_bitso import streams


def console_formatter(*, colors: bool = True) -> structlog.stdlib.ProcessorFormatter:
    """Return a console formatter for structlog.

    Args:
        colors: Whether to use colors in the console output.

    Returns:
        A structlog formatter.
    """
    return structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=colors),
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )


def json_formatter() -> structlog.stdlib.ProcessorFormatter:
    """Return a JSON formatter for structlog.

    Returns:
        A structlog formatter.
    """
    return structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.PositionalArgumentsFormatter(),
        ],
    )


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

    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams.

        Returns:
            A list of streams.
        """
        return [
            streams.BooksStream(tap=self),
            streams.LedgerStream(tap=self),
            streams.TickersStream(tap=self),
            streams.TradesStream(tap=self),
            streams.UserTradesStream(tap=self),
        ]
