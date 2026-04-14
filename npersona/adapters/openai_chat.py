"""OpenAIChatAdapter — OpenAI-compatible /v1/chat/completions shape."""

from __future__ import annotations

import json
from typing import Any

from npersona.adapters.base import HTTPRequest


class OpenAIChatAdapter:
    """OpenAI-compatible Chat API shape: {messages: [{role: "user", content: prompt}]}."""

    def __init__(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self.headers = {"Content-Type": "application/json", **(headers or {})}

    async def build_request(self, test_case: Any) -> HTTPRequest:
        """Build OpenAI chat completions request."""
        return HTTPRequest(
            method="POST",
            url=self.endpoint,
            headers=self.headers,
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": test_case.prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            timeout=30.0,
        )

    async def parse_response(self, raw_response: str) -> str:
        """Extract text from {choices: [{message: {content: ...}}]}."""
        try:
            data = json.loads(raw_response)
            if isinstance(data, dict) and "choices" in data:
                choices = data.get("choices", [])
                if choices and isinstance(choices[0], dict):
                    message = choices[0].get("message", {})
                    if isinstance(message, dict):
                        return message.get("content", raw_response)
        except (json.JSONDecodeError, (AttributeError, TypeError, KeyError)):
            pass
        return raw_response

    async def on_session_start(self) -> None:
        """No-op for stateless chat."""
        pass

    async def on_session_end(self) -> None:
        """No-op for stateless chat."""
        pass

    async def on_request_begin(self, test_case_id: str) -> None:
        """No-op for stateless chat."""
        pass

    async def on_request_end(self, test_case_id: str, success: bool) -> None:
        """No-op for stateless chat."""
        pass
