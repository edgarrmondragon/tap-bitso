"""REST client handling, including BitsoStream base class."""
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

import backoff
import requests
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.streams import RESTStream
from structlog.contextvars import bind_contextvars

from tap_bitso.auth import BitsoAuthenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BitsoStream(RESTStream):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    retry_codes = {400}

    def get_records(self, context: Optional[dict]) -> Generator[dict, None, None]:
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
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: Stream sync context.
            next_page_token: Value used to retreive the next page of results.

        Returns:
            A mapping of URL query parameters.
        """
        params: Dict[str, Any] = {}
        if next_page_token:
            params["marker"] = next_page_token
        if self.replication_key:
            params["limit"] = 100
            params["sort"] = "asc"
        if self.book_based and context:
            params["book"] = context["book"]
        return params

    def prepare_request(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> requests.PreparedRequest:
        """Prepare a request object.

        If partitioning is supported, the `context` object will contain the partition
        definitions. Pagination information can be parsed from `next_page_token` if
        `next_page_token` is not None.

        Args:
            context: Stream sync context.
            next_page_token: Value used to retreive the next page of results.

        Returns:
            A `requests.PreparedRequest`_ object.

        .. _requests.Request:
            https://docs.python-requests.org/en/latest/api/#requests.PreparedRequest
        """
        http_method = self.rest_method
        url: str = self.get_url(context)
        params: dict = self.get_url_params(context, next_page_token)
        request_data = self.prepare_request_payload(context, next_page_token)
        headers = self.http_headers

        request = requests.Request(
            method=http_method,
            url=url,
            headers=headers,
            params=params,
            data=request_data,
        )
        self.authenticator.authenticate_request(request)

        prepared_request: requests.PreparedRequest = (
            self.requests_session.prepare_request(request)
        )
        return prepared_request

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Any:
        """Return token identifying next page or None if all records have been read.

        Args:
            response: A raw `requests.Response`_ object.
            previous_token: Previous pagination reference.

        Returns:
            Reference value to retrieve next page.

        .. _requests.Response:
            https://docs.python-requests.org/en/latest/api/#requests.Response
        """
        token = super().get_next_page_token(response, previous_token)
        self.logger.debug("New page token %s", token)
        return token

    @property
    def partitions(self) -> Optional[List[dict]]:
        """Return a list of partition key dicts (if applicable), otherwise None.

        Returns:
            A list of dictionaries identifying stream partitions.
        """
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]
        return []

    def request_decorator(self, func: Callable) -> Callable:
        """Instantiate a decorator for handling request failures.

        Developers may override this method to provide custom backoff or retry
        handling.

        Args:
            func: Function to decorate.

        Returns:
            A decorated method.
        """
        decorator: Callable = backoff.on_exception(
            backoff.constant,
            (RetriableAPIError,),
            max_tries=60,
            logger=self.tap_name,
            interval=15,
        )(func)
        return decorator

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
