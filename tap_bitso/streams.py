"""Stream type classes for tap-bitso."""

from pathlib import Path

from tap_bitso.client import BitsoStream, PaginatedBitsoStream

SCHEMAS_DIR = Path(__file__).parent / "./schemas"


class LedgerStream(PaginatedBitsoStream):
    """Ledger stream."""

    name = "ledger"
    path = "/v3/ledger/"
    replication_key = "eid"
    schema_filepath = SCHEMAS_DIR / "ledger.json"


class TradesStream(PaginatedBitsoStream):
    """Trades stream."""

    name = "trades"
    path = "/v3/trades/?book=btc_mxn"
    replication_key = "tid"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class UserTradesStream(PaginatedBitsoStream):
    """User trades stream."""

    name = "user_trades"
    path = "/v3/user_trades"
    book_based = True
    replication_key = "tid"
    schema_filepath = SCHEMAS_DIR / "trade.json"


class TickersStream(BitsoStream):
    """Tickers stream."""

    name = "tickers"
    path = "/v3/ticker"
    book_based = True
    primary_keys = ["book", "created_at"]
    schema_filepath = SCHEMAS_DIR / "ticker.json"


class BooksStream(BitsoStream):
    """Books stream."""

    name = "books"
    path = "/v3/available_books/"
    primary_keys = ["book"]
    schema_filepath = SCHEMAS_DIR / "book.json"


# class TickersStream(BitsoStream):
#     """Tickers stream."""

#     name = "tickers"
#     path = "/v3/ticker/?book=btc_mxn"
#     primary_keys = ["book", "created_at"]
#     schema_filepath = SCHEMAS_DIR / "ticker.json"
#     records_jsonpath = "$.payload"
