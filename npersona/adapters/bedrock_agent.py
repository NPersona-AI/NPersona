"""BedrockAgentAdapter — AWS Bedrock Agent runtime with session state management."""

from __future__ import annotations

import json
import uuid
from typing import Any

from npersona.adapters.base import HTTPRequest


class BedrockAgentAdapter:
    """AWS Bedrock Agent adapter with per-test session management.

    Bedrock agents maintain conversational state via sessionId, enabling
    multi-turn adversarial attacks on RAG-enabled agent systems.
    """

    def __init__(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        stateful: bool = True,
    ) -> None:
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.stateful = stateful
        self._sessions: dict[str, str] = {}  # test_case_id -> session_id

    async def build_request(self, test_case: Any) -> HTTPRequest:
        """Build Bedrock agent invoke request with sessionId."""
        session_id = self._sessions.get(test_case.id, str(uuid.uuid4()))
        if self.stateful:
            self._sessions[test_case.id] = session_id

        payload = {
            "agentAliasId": "ALIS1234567890",  # User supplies or via endpoint param
            "sessionId": session_id,
            "inputText": test_case.prompt,
        }

        return HTTPRequest(
            method="POST",
            url=self.endpoint,
            headers=self.headers,
            json=payload,
            timeout=30.0,
        )

    async def parse_response(self, raw_response: str) -> str:
        """Extract text from {response: ...} or {output: ...}."""
        try:
            data = json.loads(raw_response)
            if isinstance(data, dict):
                return (
                    data.get("response")
                    or data.get("output")
                    or data.get("text")
                    or raw_response
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        return raw_response

    async def on_session_start(self) -> None:
        """Clear session cache before batch."""
        self._sessions.clear()

    async def on_session_end(self) -> None:
        """Optionally close all sessions (if Bedrock supports it)."""
        self._sessions.clear()

    async def on_request_begin(self, test_case_id: str) -> None:
        """Session is implicitly created on first invoke."""
        if test_case_id not in self._sessions and self.stateful:
            self._sessions[test_case_id] = str(uuid.uuid4())

    async def on_request_end(self, test_case_id: str, success: bool) -> None:
        """Retain session for stateful runs; clear on failure if not stateful."""
        if not success and not self.stateful:
            self._sessions.pop(test_case_id, None)
