"""Bitso tap class."""

from __future__ import annotations

import logging
import logging.config

import structlog
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

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                ],
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": [
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.PositionalArgumentsFormatter(),
                ],
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "formatter": "json",
                "filename": "tap.log",
            },
        },
        "loggers": {
            "tap-bitso": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
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
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
