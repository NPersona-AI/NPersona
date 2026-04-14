"""JsonPostAdapter — default shape: {request_field: prompt}.

Enhanced with:
- Timeout handling
- Retry logic with exponential backoff
- Better error messages
- Graceful response parsing
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from npersona.adapters.base import HTTPRequest

logger = logging.getLogger(__name__)


class JsonPostAdapter:
    """POST JSON with prompt in a custom field. Default production shape.

    Features:
    - Configurable timeouts
    - Automatic retry with exponential backoff
    - Graceful error handling
    - Better error messages
    """

    def __init__(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        request_field: str = "message",
        response_field: str = "response",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize adapter with error handling configuration.

        Args:
            endpoint: API endpoint URL
            headers: Custom HTTP headers
            request_field: JSON field name for request prompt
            response_field: JSON field name for response text
            timeout: Request timeout in seconds (default 30)
            max_retries: Maximum retry attempts for transient failures (default 3)
            retry_delay: Initial retry delay in seconds (default 1)
        """
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.request_field = request_field
        self.response_field = response_field
        self.timeout = max(5.0, min(timeout, 300.0))  # Clamp between 5-300 seconds
        self.max_retries = max(0, min(max_retries, 10))  # Clamp between 0-10
        self.retry_delay = max(0.1, min(retry_delay, 60.0))  # Clamp between 0.1-60 seconds
        self.request_count = 0
        self.retry_count = 0

    async def build_request(self, test_case: Any) -> HTTPRequest:
        """Build {request_field: prompt} POST request with timeout.

        Args:
            test_case: Test case with prompt attribute

        Returns:
            HTTPRequest with proper timeout and headers
        """
        return HTTPRequest(
            method="POST",
            url=self.endpoint,
            headers=self.headers,
            json={self.request_field: test_case.prompt},
            timeout=self.timeout,
        )

    async def parse_response(self, raw_response: str) -> str:
        """Extract response from {response_field: ...} or return full response.

        Gracefully handles:
        - Valid JSON with response_field
        - Valid JSON without response_field (returns full JSON)
        - Invalid JSON (returns raw text)
        - Empty responses

        Args:
            raw_response: Raw response text from endpoint

        Returns:
            Extracted response text
        """
        if not raw_response or not raw_response.strip():
            logger.warning("Received empty response from endpoint")
            return ""

        try:
            data = json.loads(raw_response)
            if isinstance(data, dict):
                # Try to extract response field
                if self.response_field in data:
                    response = data[self.response_field]
                    if isinstance(response, str):
                        return response
                    # If it's an object, convert to JSON string
                    return json.dumps(response)
                # Fall back to full JSON if field not found
                logger.debug(f"Response field '{self.response_field}' not found in JSON, returning full response")
                return json.dumps(data)
            elif isinstance(data, str):
                return data
            else:
                # Other JSON types (list, number, etc.)
                return json.dumps(data)
        except json.JSONDecodeError as e:
            # Not JSON, return as-is
            logger.debug(f"Response is not valid JSON, returning raw text: {e}")
            return raw_response
        except Exception as e:
            # Unexpected error, log and return raw response
            logger.error(f"Unexpected error parsing response: {e}")
            return raw_response

    async def get_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Formula: retry_delay * (2 ^ attempt) + random jitter
        Examples:
        - Attempt 0: 1 second
        - Attempt 1: 2 seconds
        - Attempt 2: 4 seconds

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        import random
        delay = self.retry_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
        return min(delay + jitter, 60.0)  # Cap at 60 seconds

    async def should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable (transient vs permanent).

        Retryable errors:
        - Timeout
        - Connection refused (endpoint temporarily down)
        - 503 Service Unavailable
        - 429 Too Many Requests (rate limited)

        Non-retryable errors:
        - 400 Bad Request
        - 401 Unauthorized
        - 404 Not Found
        - Other 4xx errors

        Args:
            error: Exception that occurred

        Returns:
            True if error is transient and should be retried
        """
        error_str = str(error).lower()

        # Transient errors (should retry)
        transient_indicators = [
            "timeout",
            "connection refused",
            "connection reset",
            "503",
            "429",
            "temporarily unavailable",
            "try again later",
        ]

        for indicator in transient_indicators:
            if indicator in error_str:
                return True

        # Permanent errors (don't retry)
        permanent_indicators = [
            "400",
            "401",
            "403",
            "404",
            "unauthorized",
            "forbidden",
            "not found",
            "invalid request",
        ]

        for indicator in permanent_indicators:
            if indicator in error_str:
                return False

        # Unknown errors: don't retry to avoid infinite loops
        return False

    async def on_session_start(self) -> None:
        """Initialize session counters."""
        self.request_count = 0
        self.retry_count = 0
        logger.debug(f"Adapter session started: {self.endpoint}")

    async def on_session_end(self) -> None:
        """Log session statistics."""
        if self.request_count > 0:
            retry_rate = (self.retry_count / self.request_count * 100) if self.request_count > 0 else 0
            logger.info(
                f"Adapter session ended: {self.request_count} requests, "
                f"{self.retry_count} retries ({retry_rate:.1f}%)"
            )

    async def on_request_begin(self, test_case_id: str) -> None:
        """Track request start."""
        self.request_count += 1
        logger.debug(f"Request {self.request_count} starting: {test_case_id}")

    async def on_request_end(self, test_case_id: str, success: bool) -> None:
        """Track request completion."""
        status = "SUCCESS" if success else "FAILED"
        logger.debug(f"Request {test_case_id} {status}")
