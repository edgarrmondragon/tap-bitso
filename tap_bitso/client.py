"""REST client handling, including BitsoStream base class."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from singer_sdk.streams import RESTStream
from structlog.contextvars import bind_contextvars
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_exponential

from tap_bitso.auth import BitsoAuthenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class RetriableAPIError(Exception):
    pass


class BitsoStream(RESTStream):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    retry_codes = {400}

    def get_records(self, context) -> None:
        bind_contextvars(context=context, stream=self.name)
        return super().get_records(context=context)

    @property
    def url_base(self) -> str:
        """Get base URL for the Bitso API from config."""
        return self.config["base_url"]

    @property
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object."""
        self.logger.info("Authenticating")
        return BitsoAuthenticator.create_for_stream(self)

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: Dict[str, Any] = {}
        if next_page_token:
            params["marker"] = next_page_token
        if self.replication_key:
            params["limit"] = 100
            params["sort"] = "asc"
        if self.book_based:
            params["book"] = context["book"]
        return params

    def prepare_request(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> requests.PreparedRequest:
        """Prepare a request object.

        If partitioning is supported, the `context` object will contain the partition
        definitions. Pagination information can be parsed from `next_page_token` if
        `next_page_token` is not None.
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
        token = super().get_next_page_token(response, previous_token)
        self.logger.debug("New page token", token=token)
        return token

    @property
    def partitions(self) -> Optional[List[dict]]:
        """Return a list of partition key dicts (if applicable), otherwise None."""
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]

    def _retry_request(self, response: requests.Response):
        """Raise an error if the response contains an error code."""
        if response.status_code in self.retry_codes:
            self.logger.info(
                "Failed request",
                status_code=response.status_code,
                content=response.content,
            )
            raise RetriableAPIError("Request failed. Retrying.")
        else:
            response.raise_for_status()

    @retry(
        reraise=True,
        wait=wait_exponential(multiplier=5, min=5, max=60),
        retry=retry_if_exception_type(RetriableAPIError),
    )
    def _request_with_backoff(
        self, prepared_request: requests.PreparedRequest, context: Optional[dict]
    ) -> requests.Response:
        self.logger.debug("HTTP Request", path=self.path)
        response = self.requests_session.send(prepared_request)
        if self._LOG_REQUEST_METRICS:
            extra_tags = {}
            if self._LOG_REQUEST_METRIC_URLS:
                extra_tags["url"] = prepared_request.path_url
            self._write_request_duration_log(
                endpoint=self.path,
                response=response,
                context=context,
                extra_tags=extra_tags,
            )
        self._retry_request(response)

        self.logger.debug("Response received successfully")
        return response


class PaginatedBitsoStream(BitsoStream):
    """A Bitso endpoint that requires pagination."""

    @property
    def primary_keys(self) -> List[str]:
        """Copy primary keys from replication key."""
        return self._primary_keys or [self.replication_key]

    @primary_keys.setter
    def primary_keys(self, value: List[str]) -> None:
        """Update primary keys from catalog file."""
        self._primary_keys = value

    @property
    def next_page_token_jsonpath(self) -> str:
        """Get JSONPath for next page token using the replication key."""
        return f"$.payload[-1].{self.replication_key}"
