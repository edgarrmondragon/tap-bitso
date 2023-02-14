"""Bitso Authentication."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from singer_sdk.authenticators import APIAuthenticatorBase

if TYPE_CHECKING:
    from requests import PreparedRequest
    from singer_sdk.streams.core import Stream

logger = logging.getLogger(__name__)


class BitsoAuthenticator(APIAuthenticatorBase):
    """Authenticator class for Bitso."""

    @classmethod
    def create_for_stream(
        cls: type[BitsoAuthenticator],
        stream: Stream,
    ) -> BitsoAuthenticator:
        """Create the authenticator for the stream.

        Args:
            stream: A Singer stream class.

        Returns:
            An authenticator instance.
        """
        return cls(stream=stream)

    def authenticate_request(
        self: BitsoAuthenticator,
        request: PreparedRequest,
    ) -> PreparedRequest:
        """Modify outgoing request with authentication data.

        See: https://bitso.com/api_info?python#creating-and-signing-requests

        Args:
            request: The `requests.PreparedRequest`_ object.

        Returns:
            The modified `requests.PreparedRequest`_ object.

        .. _requests.Request:
            https://docs.python-requests.org/en/latest/api/#requests.PreparedRequest
        """
        bitso_key: str = self.config["key"]
        bitso_secret: str = self.config["secret"]
        nonce = str(int(round(time.time() * 1000)))

        parsed = urlparse(request.url)
        method = request.method or "GET"
        path = (
            parsed.path if isinstance(parsed.path, str) else parsed.path.decode("utf-8")
        )
        message = nonce + method + path.rstrip("/")

        if method.lower() == "post" and request.body:
            message += (
                request.body
                if isinstance(request.body, str)
                else request.body.decode("utf-8")
            )

        if parsed.query:
            message += "?" + (
                parsed.query
                if isinstance(parsed.query, str)
                else parsed.query.decode("utf-8")
            )

        self.logger.debug("Signing message: %s", message)

        signature = hmac.new(
            bitso_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Update request with Bitso auth
        request.headers["Authorization"] = f"Bitso {bitso_key}:{nonce}:{signature}"

        return request
