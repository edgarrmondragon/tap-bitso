"""REST client handling, including BitsoStream base class."""

from __future__ import annotations

import typing as t
from typing import Any, Callable, Generator

import requests
import stamina
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.streams import RESTStream
from structlog.contextvars import bind_contextvars

from tap_bitso.auth import BitsoAuthenticator

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context, Record


class BitsoStream(RESTStream[str]):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    retry_codes = (400,)

    def get_records(
        self,
        context: Context | None,
    ) -> Generator[Record, None, None]:
        """Return a generator of row-type dictionary objects.

        Each row emitted should be a dictionary of property names to their values.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            One item per (possibly processed) record in the API.
        """
        bind_contextvars(context=context, stream=self.name)
        yield from super().get_records(context=context)

    @property
    def url_base(self) -> str:
        """Get base URL for the Bitso API from config.

        Returns:
            Base URL for all API requests.
        """
        return self.config["base_url"]  # type: ignore[no-any-return]

    @property
    def http_headers(self) -> dict[str, Any]:
        """Return the http headers needed.

        Returns:
            A mapping of HTTP headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_url_params(
        self,
        context: Context | None,
        next_page_token: str | None,
    ) -> dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: Stream sync context.
            next_page_token: Value used to retrieve the next page of results.

        Returns:
            A mapping of URL query parameters.
        """
        params: dict[str, Any] = {}
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
    def partitions(self) -> list[Context] | None:
        """Return a list of partition key dicts (if applicable), otherwise None.

        Returns:
            A list of dictionaries identifying stream partitions.
        """
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]
        return []

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

    def validate_response(self, response: requests.Response) -> None:
        """Validate HTTP response.

        By default, checks for error status codes (>400) and raises a
        :class:`singer_sdk.exceptions.FatalAPIError`.

        Tap developers are encouraged to override this method if their APIs use HTTP
        status codes in non-conventional ways, or if they communicate errors
        differently (e.g. in the response body).

        .. image:: ../images/200.png


        In case an error is deemed transient and can be safely retried, then this
        method should raise an :class:`singer_sdk.exceptions.RetriableAPIError`.

        Args:
            response: A `requests.Response`_ object.

        Raises:
            RetriableAPIError: If the request is retriable.

        .. _requests.Response:
            https://docs.python-requests.org/en/latest/api/#requests.Response
        """
        if response.status_code in self.retry_codes:
            raise RetriableAPIError(response.reason)

        super().validate_response(response)


class AuthenticatedBitsoStream(BitsoStream):
    """Bitso stream class with authentication."""

    @property
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object.

        Returns:
            The Bitso API authenticator object.
        """
        return BitsoAuthenticator.create_for_stream(self)
