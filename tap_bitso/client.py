"""REST client handling, including BitsoStream base class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import backoff
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.streams import RESTStream
from structlog.contextvars import bind_contextvars

from tap_bitso.auth import BitsoAuthenticator

if TYPE_CHECKING:
    import requests

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BitsoStream(RESTStream):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    retry_codes = (400,)

    def get_records(self, context: dict | None) -> Generator[dict, None, None]:
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
        return self.config["base_url"]

    @property
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object.

        Returns:
            The Bitso API authenticator object.
        """
        return BitsoAuthenticator.create_for_stream(self)

    @property
    def http_headers(self) -> dict:
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
        context: dict | None,
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
    def partitions(self) -> list[dict] | None:
        """Return a list of partition key dicts (if applicable), otherwise None.

        Returns:
            A list of dictionaries identifying stream partitions.
        """
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]
        return []

    def backoff_max_tries(self) -> int:
        """Return the maximum number of retries for a request.

        Returns:
            The maximum number of retries for a request.
        """
        return 10

    def backoff_wait_generator(self) -> Generator[float, Any, None]:
        """Return a generator of backoff wait times.

        Returns:
            A generator of backoff wait times.
        """
        return backoff.constant(interval=60)

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
