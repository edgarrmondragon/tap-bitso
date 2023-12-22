"""Stream type classes for tap-bitso."""

from __future__ import annotations

import sys
import typing as t

from tap_bitso import schemas
from tap_bitso.client import BitsoStream

if sys.version_info >= (3, 9):
    from importlib import resources as importlib_resources
else:
    import importlib_resources

SCHEMAS_DIR = importlib_resources.files(schemas)


class LedgerStream(BitsoStream):
    """Ledger stream.

    DEPRECATED.
    """

    name = "ledger"
    path = "/v3/ledger"
    replication_key = "eid"
    primary_keys: t.ClassVar[list[str]] = ["eid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "ledger.json"  # type: ignore[assignment]


class TradesStream(BitsoStream):
    """Trades stream."""

    name = "trades"
    path = "/v3/trades"
    book_based = True
    replication_key = "tid"
    primary_keys: t.ClassVar[list[str]] = ["tid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"  # type: ignore[assignment]


class UserTradesStream(BitsoStream):
    """User trades stream."""

    name = "user_trades"
    path = "/v3/user_trades"
    book_based = True
    replication_key = "tid"
    primary_keys: t.ClassVar[list[str]] = ["tid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"  # type: ignore[assignment]


class TickersStream(BitsoStream):
    """Tickers stream."""

    name = "tickers"
    path = "/v3/ticker"
    book_based = True
    records_jsonpath = "$.payload"
    primary_keys: t.ClassVar[list[str]] = ["book", "created_at"]
    schema_filepath = SCHEMAS_DIR / "ticker.json"  # type: ignore[assignment]


class BooksStream(BitsoStream):
    """Books stream."""

    name = "books"
    path = "/v3/available_books"
    primary_keys: t.ClassVar[list[str]] = ["book"]
    schema_filepath = SCHEMAS_DIR / "book.json"  # type: ignore[assignment]
