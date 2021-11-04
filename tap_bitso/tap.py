"""Bitso tap class."""

import logging
from typing import List

import structlog
from singer_sdk import Stream, Tap
from singer_sdk import typing as th
from singer_sdk.helpers._classproperty import classproperty
from structlog.contextvars import bind_contextvars, merge_contextvars

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

structlog.configure(
    processors=[
        merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }
)


class TapBitso(Tap):
    """Bitso tap class."""

    name = "tap-bitso"

    config_jsonschema = th.PropertiesList(
        th.Property("key", th.StringType, required=True),
        th.Property("secret", th.StringType, required=True),
        th.Property("base_url", th.StringType, default="https://api.bitso.com"),
        th.Property("books", th.ArrayType(th.StringType), default=["btc_mxn"]),
    ).to_dict()

    @classproperty
    def logger(cls) -> logging.Logger:
        """Get tap logger."""
        bind_contextvars(tap=cls.name, version=cls.plugin_version)
        return structlog.get_logger(cls.name)

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
