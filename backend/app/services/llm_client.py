"""Multi-provider LLM client – supports Gemini, Groq, and OpenAI.

Set LLM_PROVIDER=gemini|groq|openai in your .env file.
"""
import asyncio
import json
import logging
import re
import sys
from typing import Any

try:
    import orjson
except ImportError:
    orjson = None

from app.config import settings

logger = logging.getLogger(__name__)

# ── Retry config ────────────────────────────────────────────────────────────
_MAX_RETRIES = 5
_RETRY_DELAYS = [15, 30, 60, 90, 120]  # seconds between retries on 429


# ── Client factories (no caching — always use current settings key) ──────────

def _get_openai():
    from openai import AsyncOpenAI
    import httpx
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        max_retries=0,  # we handle retries ourselves
        timeout=httpx.Timeout(180.0, connect=30.0),  # 3 min for large persona batches
    )


def _get_azure_openai():
    from openai import AsyncAzureOpenAI
    import httpx
    return AsyncAzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        max_retries=0,
        timeout=httpx.Timeout(180.0, connect=30.0),  # 3 min for large persona batches
    )


def _get_groq():
    from groq import AsyncGroq
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


def _get_gemini():
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai


# ── JSON extraction helper ──────────────────────────────────────────────────

def _extract_json(content: str) -> dict | list:
    """Extract JSON from LLM response – handles markdown code fences.

    Uses orjson (non-recursive) for deep nesting. Falls back to standard json
    with increased recursion limit if orjson unavailable.
    """
    content = content.strip()

    # Strip markdown fences if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    match = re.search(fence_pattern, content)
    if match:
        content = match.group(1).strip()

    # Try orjson first (non-recursive, handles deep nesting)
    if orjson:
        try:
            return orjson.loads(content)
        except Exception as e:
            logger.debug(f"orjson parse failed, trying recovery: {e}")

    # Try standard json with increased recursion limit (for very deep nesting)
    try:
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, 10000))
        try:
            return json.loads(content)
        finally:
            sys.setrecursionlimit(old_limit)
    except (json.JSONDecodeError, RecursionError) as e:
        # Try extracting JSON substring as fallback
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = content.find(start_char)
            end = content.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    if orjson:
                        return orjson.loads(content[start:end + 1])
                    old_limit = sys.getrecursionlimit()
                    sys.setrecursionlimit(max(old_limit, 10000))
                    try:
                        return json.loads(content[start:end + 1])
                    finally:
                        sys.setrecursionlimit(old_limit)
                except Exception:
                    pass

        logger.error(f"JSON parse error: {e}\nContent snippet: {content[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")


def _is_rate_limit_error(e: Exception) -> tuple[bool, int]:
    """Returns (is_rate_limit, retry_after_seconds)."""
    err_str = str(e).lower()
    is_429 = "429" in str(e) or "rate_limit" in err_str or "quota" in err_str or "resource_exhausted" in err_str

    # Try to extract retryDelay from the error message
    retry_after = 60  # default
    import re as _re
    match = _re.search(r'retry[_\s]?(?:after|delay)[\":\s]+(\d+)', str(e), _re.IGNORECASE)
    if match:
        retry_after = int(match.group(1)) + 5  # add 5s buffer

    return is_429, retry_after


# ── Provider implementations ────────────────────────────────────────────────

async def _call_openai(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_openai()
    kwargs: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    usage = response.usage
    logger.info(
        f"OpenAI ({settings.OPENAI_MODEL}): "
        f"{getattr(usage, 'prompt_tokens', '?')}→{getattr(usage, 'completion_tokens', '?')} tokens"
    )
    return content


async def _call_groq(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_groq()
    effective_system = system_prompt + "\n\nRespond with valid JSON only." if json_mode else system_prompt
    kwargs: dict[str, Any] = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": effective_system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        usage = response.usage
        logger.info(
            f"Groq ({settings.GROQ_MODEL}): "
            f"{getattr(usage, 'prompt_tokens', '?')}→{getattr(usage, 'completion_tokens', '?')} tokens"
        )
        return content
    except Exception as e:
        # Groq throws 400 json_validate_failed when the model produces subtly invalid JSON.
        # The error contains the raw output in 'failed_generation' — try parsing that first.
        # If it's unparseable, fall back to a call without strict JSON mode.
        if "json_validate_failed" in str(e) and json_mode:
            logger.warning(f"Groq json_validate_failed — attempting recovery from failed_generation")
            # Extract failed_generation from the error dict
            try:
                import ast
                err_str = str(e)
                fg_match = re.search(r"'failed_generation':\s*'(.*?)'(?:\s*[,}])", err_str, re.DOTALL)
                if fg_match:
                    raw = fg_match.group(1).encode().decode("unicode_escape")
                    return raw  # pass to _extract_json in call_llm
            except Exception:
                pass
            # Final fallback: retry without response_format (prompt-only JSON mode)
            logger.warning("Groq recovery: retrying without response_format constraint")
            fallback_kwargs = {**kwargs}
            fallback_kwargs.pop("response_format", None)
            response = await client.chat.completions.create(**fallback_kwargs)
            return response.choices[0].message.content or ""
        raise


async def _call_azure_openai(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_azure_openai()
    kwargs: dict[str, Any] = {
        "model": settings.AZURE_OPENAI_DEPLOYMENT,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    usage = response.usage
    logger.info(
        f"Azure OpenAI ({settings.AZURE_OPENAI_DEPLOYMENT}): "
        f"{getattr(usage, 'prompt_tokens', '?')}→{getattr(usage, 'completion_tokens', '?')} tokens"
    )
    return content


async def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    import google.generativeai as genai
    _get_gemini()  # configure with current key

    generation_config = genai.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=generation_config,
    )

    response = await model.generate_content_async(user_prompt)
    content = response.text or ""
    logger.info(f"Gemini ({settings.GEMINI_MODEL}): {len(content)} chars")
    return content


# ── Public API ──────────────────────────────────────────────────────────────

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    json_mode: bool = True,
) -> dict[str, Any] | list | str:
    """Call the configured LLM provider with automatic retry on rate limits & JSON errors.

    Retries up to 5 times on:
    - 429/quota rate limit errors (with exponential backoff)
    - JSON parsing errors (e.g., recursion limit, malformed output)

    This handles transient failures transparently.
    """
    if max_tokens is None:
        max_tokens = settings.LLM_MAX_OUTPUT_TOKENS

    provider = settings.LLM_PROVIDER.lower()
    logger.info(f"[LLM] {provider} | json={json_mode} | temp={temperature} | max_tokens={max_tokens}")

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if provider == "gemini":
                raw = await _call_gemini(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            elif provider == "groq":
                raw = await _call_groq(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            elif provider == "azure":
                raw = await _call_azure_openai(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            else:
                raw = await _call_openai(system_prompt, user_prompt, temperature, max_tokens, json_mode)

            if not json_mode:
                return raw
            return _extract_json(raw)

        except (ValueError, RecursionError) as e:
            # JSON parsing error — retry with slightly lower temperature
            if attempt < _MAX_RETRIES:
                logger.warning(
                    f"[LLM] JSON parse error on attempt {attempt}/{_MAX_RETRIES}: {e}. "
                    f"Retrying with lower temperature..."
                )
                # Reduce temperature to encourage more deterministic output
                temperature = max(0.1, temperature - 0.1)
                last_error = e
                await asyncio.sleep(5)  # brief pause before retry
                continue
            raise

        except Exception as e:
            is_rate_limit, retry_after = _is_rate_limit_error(e)

            if is_rate_limit and attempt < _MAX_RETRIES:
                wait = max(retry_after, _RETRY_DELAYS[attempt - 1])
                logger.warning(
                    f"[LLM] Rate limit on attempt {attempt}/{_MAX_RETRIES}. "
                    f"Waiting {wait}s before retry..."
                )
                await asyncio.sleep(wait)
                last_error = e
                continue

            # Not a rate limit or JSON error, or exhausted retries
            raise

    raise last_error


async def call_llm_streaming(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
):
    """Stream LLM response token by token (OpenAI/Groq only; Gemini falls back to single call)."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "azure":
        client = _get_azure_openai()
        stream = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    elif provider == "groq":
        client = _get_groq()
        stream = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    elif provider == "gemini":
        import google.generativeai as genai
        _get_gemini()
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_prompt,
        )
        async for chunk in await model.generate_content_async(user_prompt, stream=True):
            if chunk.text:
                yield chunk.text

    else:
        client = _get_openai()
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
