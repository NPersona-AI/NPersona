"""Abstract RequestAdapter protocol — defines how to communicate with different target systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class HTTPRequest:
    """A prepared HTTP request ready to send."""

    method: str  # "GET", "POST", etc.
    url: str
    headers: dict[str, str]
    json: dict[str, Any] | None = None
    timeout: float = 30.0


class RequestAdapter(Protocol):
    """Protocol for adapting test cases into HTTP requests for different target systems."""

    async def build_request(self, test_case: Any) -> HTTPRequest:
        """Convert a TestCase into an HTTPRequest.

        Args:
            test_case: npersona.models.test_suite.TestCase

        Returns:
            HTTPRequest ready to send via httpx

        Raises:
            ValueError: If test_case is malformed or cannot be adapted
        """
        ...

    async def parse_response(self, raw_response: str) -> str:
        """Extract the text content from a raw HTTP response body.

        Args:
            raw_response: Response body as string (e.g. JSON or plain text)

        Returns:
            Extracted text content (e.g. the assistant's reply)

        Raises:
            ValueError: If response format is unexpected
        """
        ...

    async def on_session_start(self) -> None:
        """Called once before any requests are sent. For session initialization."""
        ...

    async def on_session_end(self) -> None:
        """Called once after all requests complete. For cleanup."""
        ...

    async def on_request_begin(self, test_case_id: str) -> None:
        """Called before each individual request. For per-test setup (e.g., conversation context)."""
        ...

    async def on_request_end(self, test_case_id: str, success: bool) -> None:
        """Called after each individual request. For per-test cleanup."""
        ...
