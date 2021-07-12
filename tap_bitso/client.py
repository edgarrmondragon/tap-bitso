"""REST client handling, including BitsoStream base class."""

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
from urllib.parse import urlencode

import requests
from singer_sdk.streams import RESTStream

from tap_bitso.auth import BitsoAuthenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class BitsoStream(RESTStream):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False

    @property
    def url_base(self) -> str:
        """Get base URL for the Bitso API from config."""
        return self.config["base_url"]

    @property
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object."""
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

    @property
    def partitions(self) -> Optional[List[dict]]:
        """Return a list of partition key dicts (if applicable), otherwise None."""
        if self.book_based:
            return [{"book": book} for book in self.config["books"]]


class PaginatedBitsoStream(BitsoStream):
    """A Bitso endpoint that requires pagination."""

    @property
    def primary_keys(self) -> List[str]:
        """Copy primary keys from replication key."""
        return self._primary_keys or [self.replication_key]

    @primary_keys.setter
    def primary_keys(self, value: List[str]) -> None:
        """Update primay keys from catalog file."""
        self._primary_keys = value

    @property
    def next_page_token_jsonpath(self) -> str:
        """Get JSONPath for next page token using the replication key."""
        return f"$.payload[-1].{self.replication_key}"
