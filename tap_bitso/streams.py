"""Stream type classes for tap-bitso."""

from __future__ import annotations

import singer_sdk.typing as th

from tap_bitso.client import AuthenticatedBitsoStream, BitsoStream


class LedgerStream(AuthenticatedBitsoStream):
    """Ledger stream.

    DEPRECATED.
    """

    name = "ledger"
    path = "/v3/ledger"
    replication_key = "eid"
    primary_keys = ("eid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema = th.PropertiesList(
        th.Property("eid", th.StringType, required=True),
        th.Property(
            "balance_updates",
            th.ArrayType(
                th.ObjectType(
                    th.Property("amount", th.StringType, required=True),
                    th.Property("currency", th.StringType, required=True),
                )
            ),
            required=True,
        ),
        th.Property("created_at", th.DateTimeType, required=True),
        th.Property(
            "details",
            th.ObjectType(
                th.Property(
                    "tid",
                    th.IntegerType,
                ),
                th.Property(
                    "fid",
                    th.StringType,
                    nullable=False,
                    examples=["31c9933e892aed075ce3bd7620faf1bc"],
                ),
                th.Property(
                    "asset",
                    th.StringType,
                    nullable=False,
                    examples=["mxn"],
                ),
                th.Property(
                    "method",
                    th.StringType,
                    nullable=False,
                    examples=["sp"],
                ),
                th.Property(
                    "network",
                    th.StringType,
                    nullable=False,
                    examples=["spei"],
                ),
                th.Property(
                    "protocol",
                    th.StringType,
                    nullable=False,
                    examples=["clabe"],
                ),
                th.Property(
                    "integration",
                    th.StringType,
                    nullable=False,
                    examples=["stp"],
                ),
                th.Property(
                    "method_name",
                    th.StringType,
                    nullable=False,
                    examples=["SPEI Transfer"],
                ),
                th.Property(
                    "oid",
                    th.StringType,
                    nullable=False,
                    examples=["ffKrqpCbL8H7CvEy"],
                ),
                th.Property(
                    "qid",
                    th.StringType,
                    nullable=False,
                    examples=["kEFa1r4U"],
                ),
            ),
        ),
        th.Property("operation", th.StringType, required=True),
    ).to_dict()


class TradesStream(BitsoStream):
    """Trades stream."""

    name = "trades"
    path = "/v3/trades"
    book_based = True
    replication_key = "tid"
    primary_keys = ("tid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema = th.PropertiesList(
        th.Property(
            "book",
            th.StringType,
            examples=["btc_mxn"],
            required=True,
        ),
        th.Property(
            "created_at",
            th.DateTimeType,
            examples=["2016-04-08T17:52:31.000+00:00"],
            required=True,
        ),
        th.Property(
            "amount",
            th.StringType,
            examples=["0.02000000"],
            required=True,
        ),
        th.Property(
            "maker_side",
            th.StringType,
            examples=["buy", "sell"],
            required=True,
        ),
        th.Property(
            "price",
            th.StringType,
            examples=["5545.01"],
            required=True,
        ),
        th.Property(
            "tid",
            th.IntegerType,
            examples=[55845],
            required=True,
        ),
    ).to_dict()


class UserTradesStream(AuthenticatedBitsoStream):
    """User trades stream."""

    name = "user_trades"
    path = "/v3/user_trades"
    book_based = True
    replication_key = "tid"
    primary_keys = ("tid",)
    next_page_token_jsonpath = f"$.payload[-1].{replication_key}"
    schema = TradesStream.schema


class TickersStream(BitsoStream):
    """Tickers stream."""

    name = "tickers"
    path = "/v3/ticker"
    book_based = True
    records_jsonpath = "$.payload"
    primary_keys = ("book", "created_at")
    schema = th.PropertiesList(
        th.Property("book", th.StringType, examples=["btc_mxn"], required=True),
        th.Property("volume", th.StringType, examples=["22.31349615"], required=True),
        th.Property("high", th.StringType, examples=["5750.00"], required=True),
        th.Property("last", th.StringType, examples=["5633.98"], required=True),
        th.Property("low", th.StringType, examples=["5545.01"], required=True),
        th.Property("vwap", th.StringType, examples=["5633.98"], required=True),
        th.Property("ask", th.StringType, examples=["5633.98"], required=True),
        th.Property("bid", th.StringType, examples=["5633.98"], required=True),
        th.Property("change_24", th.StringType, examples=["0.01"], required=True),
        th.Property(
            "created_at",
            th.DateTimeType,
            examples=["2016-04-08T17:52:31.000+00:00"],
            required=True,
        ),
        th.Property(
            "rolling_average_change",
            th.ObjectType(
                th.Property("6", th.StringType, examples=["-0.5228"]),
            ),
            required=True,
        ),
    ).to_dict()


class BooksStream(BitsoStream):
    """Books stream."""

    name = "books"
    path = "/v3/available_books"
    primary_keys = ("book",)
    schema = th.PropertiesList(
        th.Property(
            "book",
            th.StringType,
            examples=["btc_mxn"],
            required=True,
        ),
        th.Property(
            "minimum_amount",
            th.StringType,
            examples=["0.001"],
            required=True,
        ),
        th.Property(
            "maximum_amount",
            th.StringType,
            examples=["1000000"],
            required=True,
        ),
        th.Property(
            "minimum_price",
            th.StringType,
            examples=["0.001"],
            required=True,
        ),
        th.Property(
            "maximum_price",
            th.StringType,
            examples=["1000000"],
            required=True,
        ),
        th.Property(
            "minimum_value",
            th.StringType,
            examples=["0.001"],
            required=True,
        ),
        th.Property(
            "maximum_value",
            th.StringType,
            examples=["1000000"],
            required=True,
        ),
        th.Property(
            "tick_size",
            th.StringType,
            examples=["0.01"],
            required=True,
        ),
        th.Property(
            "default_chart",
            th.StringType,
            examples=["candle"],
            required=True,
        ),
        th.Property(
            "fees",
            th.ObjectType(
                th.Property(
                    "flat_rate",
                    th.ObjectType(
                        th.Property(
                            "maker",
                            th.StringType,
                            examples=["0.001"],
                            nullable=False,
                            required=True,
                        ),
                        th.Property(
                            "taker",
                            th.StringType,
                            examples=["0.001"],
                            nullable=False,
                            required=True,
                        ),
                        additional_properties=True,
                    ),
                    required=True,
                ),
                th.Property(
                    "structure",
                    th.ArrayType(
                        th.ObjectType(
                            th.Property(
                                "volume",
                                th.StringType,
                                examples=["0.001"],
                                nullable=False,
                                required=True,
                            ),
                            th.Property(
                                "maker",
                                th.StringType,
                                examples=["0.001"],
                                nullable=False,
                                required=True,
                            ),
                            th.Property(
                                "taker",
                                th.StringType,
                                examples=["0.001"],
                                nullable=False,
                                required=True,
                            ),
                        )
                    ),
                    examples=[
                        [
                            {
                                "volume": "1500000",
                                "maker": "0.00500",
                                "taker": "0.00650",
                            },
                        ]
                    ],
                ),
                additional_properties=True,
            ),
            required=True,
        ),
        additional_properties=True,
    ).to_dict()
