"""CustomCallableAdapter — user-supplied async callable for arbitrary target shapes."""

from __future__ import annotations

from typing import Any, Callable

from npersona.adapters.base import HTTPRequest


class CustomCallableAdapter:
    """Wrap a user-supplied async callable to bridge arbitrary target shapes.

    The user provides:
        build_request: async def(test_case) -> HTTPRequest
        parse_response: async def(raw_response: str) -> str

    Optionally:
        on_session_start, on_session_end, on_request_begin, on_request_end
    """

    def __init__(
        self,
        build_request: Callable[[Any], Any],
        parse_response: Callable[[str], Any],
        on_session_start: Callable[[], Any] | None = None,
        on_session_end: Callable[[], Any] | None = None,
        on_request_begin: Callable[[str], Any] | None = None,
        on_request_end: Callable[[str, bool], Any] | None = None,
    ) -> None:
        self._build_request = build_request
        self._parse_response = parse_response
        self._on_session_start = on_session_start or (lambda: None)
        self._on_session_end = on_session_end or (lambda: None)
        self._on_request_begin = on_request_begin or (lambda tid: None)
        self._on_request_end = on_request_end or (lambda tid, ok: None)

    async def build_request(self, test_case: Any) -> HTTPRequest:
        """Delegate to user's build_request callable."""
        result = self._build_request(test_case)
        if hasattr(result, "__await__"):
            return await result
        return result

    async def parse_response(self, raw_response: str) -> str:
        """Delegate to user's parse_response callable."""
        result = self._parse_response(raw_response)
        if hasattr(result, "__await__"):
            return await result
        return result

    async def on_session_start(self) -> None:
        """Delegate to user's on_session_start (if provided)."""
        result = self._on_session_start()
        if hasattr(result, "__await__"):
            await result

    async def on_session_end(self) -> None:
        """Delegate to user's on_session_end (if provided)."""
        result = self._on_session_end()
        if hasattr(result, "__await__"):
            await result

    async def on_request_begin(self, test_case_id: str) -> None:
        """Delegate to user's on_request_begin (if provided)."""
        result = self._on_request_begin(test_case_id)
        if hasattr(result, "__await__"):
            await result

    async def on_request_end(self, test_case_id: str, success: bool) -> None:
        """Delegate to user's on_request_end (if provided)."""
        result = self._on_request_end(test_case_id, success)
        if hasattr(result, "__await__"):
            await result
