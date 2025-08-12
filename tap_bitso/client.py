"""REST client handling, including BitsoStream base class."""

from __future__ import annotations

import sys
import typing as t
from http import HTTPStatus

import requests
import requests.exceptions
import stamina
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.streams import RESTStream

from tap_bitso.auth import BitsoAuthenticator

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


if t.TYPE_CHECKING:
    from collections.abc import Callable

    from singer_sdk.helpers.types import Context


class BitsoStream(RESTStream[str]):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    extra_retry_statuses = (HTTPStatus.BAD_REQUEST,)

    @property
    @override
    def url_base(self) -> str:
        """Get base URL for the Bitso API from config.

        Returns:
            Base URL for all API requests.
        """
        return self.config["base_url"]  # type: ignore[no-any-return]

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: str | None,
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: Stream sync context.
            next_page_token: Value used to retrieve the next page of results.

        Returns:
            A mapping of URL query parameters.
        """
        params: dict[str, t.Any] = {}
        marker = self.get_starting_replication_key_value(context)

        if next_page_token:
            params["marker"] = next_page_token
        elif marker:
            params["marker"] = marker
        if self.replication_key:
            params["limit"] = 100
            params["sort"] = "asc"
        if self.book_based and context:
            params["book"] = context["book"]
        return params

    @property
    def partitions(self) -> list[dict[str, t.Any]] | None:
        """Return a list of partition key dicts (if applicable), otherwise None.

        Returns:
            A list of dictionaries identifying stream partitions.
        """
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]
        return []

    @override
    def request_decorator(self, func: Callable) -> Callable:  # type: ignore[type-arg]
        """Return a decorator for a request function.

        Args:
            func: The function to decorate.

        Returns:
            A decorated function.
        """
        return stamina.retry(
            on=(
                ConnectionResetError,
                RetriableAPIError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ContentDecodingError,
            ),
            attempts=10,
            timeout=600,
            wait_initial=60,
            wait_max=300,
            wait_jitter=5,
            wait_exp_base=1.1,
        )(func)


class AuthenticatedBitsoStream(BitsoStream):
    """Bitso stream class with authentication."""

    @property
    @override
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object.

        Returns:
            The Bitso API authenticator object.
        """
        return BitsoAuthenticator.create_for_stream(self)
