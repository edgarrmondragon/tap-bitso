"""REST client handling, including BitsoStream base class."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import structlog
from singer_sdk.streams import RESTStream
from singer_sdk.tap_base import Tap
from structlog import get_logger
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_exponential

from tap_bitso.auth import BitsoAuthenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
pre_chain = [
    structlog.stdlib.add_log_level,
    timestamper,
]

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "json": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


class RetriableAPIError(Exception):
    pass


class BitsoStream(RESTStream):
    """Bitso stream class."""

    records_jsonpath = "$.payload[*]"
    book_based = False
    retry_codes = {400}

    def __init__(self, tap: Tap, *args, **kwargs):
        super().__init__(tap, *args, **kwargs)
        self._log: structlog.stdlib.BoundLogger = get_logger(
            tap=tap,
            url=self.url_base,
            stream=self.name,
        )

    @property
    def url_base(self) -> str:
        """Get base URL for the Bitso API from config."""
        return self.config["base_url"]

    @property
    def authenticator(self) -> BitsoAuthenticator:
        """Return a new authenticator object."""
        self._log.debug("Authentication")
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

    def _retry_request(self, response: requests.Response):
        """Raise an error if the response contains an error code."""
        if response.status_code in self.retry_codes:
            self._log.debug(
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
        self._log.debug("HTTP Request", path=self.path)
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

        self._log.debug("Response received successfully")
        return response


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
