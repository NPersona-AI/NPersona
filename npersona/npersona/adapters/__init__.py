"""Target-system request adapters — normalize how the Executor talks to different AI APIs."""

from npersona.adapters.base import HTTPRequest, RequestAdapter
from npersona.adapters.bedrock_agent import BedrockAgentAdapter
from npersona.adapters.custom import CustomCallableAdapter
from npersona.adapters.json_post import JsonPostAdapter
from npersona.adapters.openai_chat import OpenAIChatAdapter

__all__ = [
    "HTTPRequest",
    "RequestAdapter",
    "JsonPostAdapter",
    "OpenAIChatAdapter",
    "BedrockAgentAdapter",
    "CustomCallableAdapter",
    "build_adapter",
]


def build_adapter(config) -> RequestAdapter:
    """Construct the adapter referenced by ``config.executor_adapter``."""
    name = config.executor_adapter
    if name == "json-post":
        return JsonPostAdapter(
            endpoint=config.system_endpoint,
            headers=config.system_headers,
            request_field=config.request_field,
            response_field=config.response_field,
        )
    if name == "openai-chat":
        return OpenAIChatAdapter(
            endpoint=config.system_endpoint,
            headers=config.system_headers,
        )
    if name == "bedrock-agent":
        return BedrockAgentAdapter(
            endpoint=config.system_endpoint,
            headers=config.system_headers,
            stateful=config.stateful_session,
        )
    if name == "custom":
        raise ValueError(
            "executor_adapter='custom' requires passing a CustomCallableAdapter "
            "directly to Executor(adapter=...); it cannot be built from config alone."
        )
    raise ValueError(f"Unknown executor_adapter: {name!r}")
