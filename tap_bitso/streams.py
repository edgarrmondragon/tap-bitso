"""Stream type classes for tap-bitso."""

from __future__ import annotations

import sys

from tap_bitso import schemas
from tap_bitso.client import AuthenticatedBitsoStream, BitsoStream

if sys.version_info >= (3, 9):
    from importlib import resources as importlib_resources
else:
    import importlib_resources

SCHEMAS_DIR = importlib_resources.files(schemas)


class LedgerStream(AuthenticatedBitsoStream):
    """Ledger stream.

    DEPRECATED.
    """

    name = "ledger"
    path = "/v3/ledger"
    replication_key = "eid"
    primary_keys = ("eid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "ledger.json"


class TradesStream(BitsoStream):
    """Trades stream."""

    name = "trades"
    path = "/v3/trades"
    book_based = True
    replication_key = "tid"
    primary_keys = ("tid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class UserTradesStream(AuthenticatedBitsoStream):
    """User trades stream."""

    name = "user_trades"
    path = "/v3/user_trades"
    book_based = True
    replication_key = "tid"
    primary_keys = ("tid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class TickersStream(BitsoStream):
    """Tickers stream."""

    name = "tickers"
    path = "/v3/ticker"
    book_based = True
    records_jsonpath = "$.payload"
    primary_keys = ("book", "created_at")
    schema_filepath = SCHEMAS_DIR / "ticker.json"


class BooksStream(BitsoStream):
    """Books stream."""

    name = "books"
    path = "/v3/available_books"
    primary_keys = ("book",)
    schema_filepath = SCHEMAS_DIR / "book.json"
