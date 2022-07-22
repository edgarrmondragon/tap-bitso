"""Bitso Authentication."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from requests import Request
from singer_sdk.authenticators import APIAuthenticatorBase
from singer_sdk.streams.core import Stream


class BitsoAuthenticator(APIAuthenticatorBase):
    """Authenticator class for Bitso."""

    @classmethod
    def create_for_stream(cls, stream: Stream) -> "BitsoAuthenticator":
        """Create the authenticator for the stream.

        Args:
            stream: A Singer stream class.

        Returns:
            An authenticator instance.
        """
        return cls(stream=stream)

    def authenticate_request(self: "BitsoAuthenticator", request: Request) -> None:
        """Modify outgoing request with authentication data.

        See: https://bitso.com/api_info?python#creating-and-signing-requests

        Args:
            request: The `requests.Request`_ object.

        .. _requests.Request:
            https://docs.python-requests.org/en/latest/api/#requests.Request
        """
        bitso_key: str = self.config["key"]
        bitso_secret: str = self.config["secret"]
        nonce = str(int(round(time.time() * 1000)))

        _, path = request.url.split(self.config["base_url"])
        message = nonce + request.method + path

        if request.method.lower() == "post":
            message += json.dumps(request.data)

        if request.params:
            message += "?" + urlencode(request.params)

        signature = hmac.new(
            bitso_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        auth_header = f"Bitso {bitso_key}:{nonce}:{signature}"

        # Update request with Bitso auth
        request.headers.update({"Authorization": auth_header})
