"""Stream type classes for tap-bitso."""

from __future__ import annotations

import typing as t
from pathlib import Path

from tap_bitso.client import BitsoStream

SCHEMAS_DIR = Path(__file__).parent / "./schemas"


class LedgerStream(BitsoStream):
    """Ledger stream."""

    name = "ledger"
    path = "/v3/ledger"
    replication_key = "eid"
    primary_keys: t.ClassVar[list[str]] = ["eid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "ledger.json"


class TradesStream(BitsoStream):
    """Trades stream."""

    name = "trades"
    path = "/v3/trades"
    book_based = True
    replication_key = "tid"
    primary_keys: t.ClassVar[list[str]] = ["tid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class UserTradesStream(BitsoStream):
    """User trades stream."""

    name = "user_trades"
    path = "/v3/user_trades"
    book_based = True
    replication_key = "tid"
    primary_keys: t.ClassVar[list[str]] = ["tid"]
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class TickersStream(BitsoStream):
    """Tickers stream."""

    name = "tickers"
    path = "/v3/ticker"
    book_based = True
    records_jsonpath = "$.payload"
    primary_keys: t.ClassVar[list[str]] = ["book", "created_at"]
    schema_filepath = SCHEMAS_DIR / "ticker.json"


class BooksStream(BitsoStream):
    """Books stream."""

    name = "books"
    path = "/v3/available_books"
    primary_keys: t.ClassVar[list[str]] = ["book"]
    schema_filepath = SCHEMAS_DIR / "book.json"
