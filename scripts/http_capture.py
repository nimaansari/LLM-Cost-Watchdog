"""
HTTP-layer capture: log LLM calls without wrapping any SDK.

The modern Python SDKs (openai, anthropic, google-genai, cohere, mistralai)
all use `httpx` under the hood. Monkey-patching httpx's transport lets us
observe every LLM HTTP request and response from those SDKs — no user code
changes needed.

Usage:
    from http_capture import install_global_capture
    install_global_capture()   # call once at process start

How it works (and why the naive version didn't):
    At the transport layer (`HTTPTransport.handle_request`) the response body
    has NOT been read yet — touching `response.content` raises
    `httpx.ResponseNotRead`, so the old "read response.content here" approach
    captured nothing for normal (non-streaming) calls. Instead we wrap
    `response.stream` with a tee that buffers the raw bytes as the SDK reads
    them, and parses usage once the stream is fully consumed. The SDK still
    gets its bytes untouched.

    The buffered bytes are content-encoded (gzip/deflate/br), so we decode
    using the `Content-Encoding` header before parsing JSON.

Not captured:
    - SDKs that use `requests`/`urllib3` directly (older Cohere, boto3).
      Use the per-SDK wrappers in tracker.py for those.
    - Streaming responses (text/event-stream): usage arrives in a final SSE
      chunk owned by the caller; we record the gap instead of guessing.

This is best-effort telemetry. For strict billing you still want the
provider's own dashboard.
"""
from __future__ import annotations

import gzip
import json
import sys
import zlib
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import usage_log  # noqa: E402
import _pricing   # noqa: E402


# (host_suffix, provider_tag)
_KNOWN_HOSTS = [
    ("api.anthropic.com", "anthropic"),
    ("api.openai.com", "openai"),
    ("openrouter.ai", "openrouter"),
    ("api.mistral.ai", "mistral"),
    ("api.cohere.com", "cohere"),
    ("api.cohere.ai", "cohere"),
    ("api.deepseek.com", "deepseek"),
    ("api.groq.com", "groq"),
    ("generativelanguage.googleapis.com", "google"),
    ("api.x.ai", "xai"),
    ("api.together.xyz", "together"),
    ("api.fireworks.ai", "fireworks"),
    ("api.perplexity.ai", "perplexity"),
]

# Cap how much we buffer per response (bytes). LLM JSON bodies are tiny; this
# guards against teeing a huge non-LLM download that shares a known host.
_MAX_BUFFER = 2 * 1024 * 1024


def _classify_host(host: str) -> Optional[str]:
    host = host.lower()
    for suffix, tag in _KNOWN_HOSTS:
        if host.endswith(suffix):
            return tag
    return None


def _decode_body(content_encoding: str, raw: bytes) -> Optional[bytes]:
    """Decode a content-encoded body. Returns None if we can't."""
    enc = (content_encoding or "").lower().strip()
    try:
        if enc in ("", "identity"):
            return raw
        if enc == "gzip":
            return gzip.decompress(raw)
        if enc == "deflate":
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return zlib.decompress(raw, -zlib.MAX_WBITS)
        if enc == "br":
            try:
                import brotli  # type: ignore
            except ImportError:
                return None
            return brotli.decompress(raw)
    except (OSError, zlib.error, ValueError):
        return None
    # Unknown encoding (e.g. "zstd") — give up gracefully.
    return None


def _extract_model_and_usage(provider: str, body: dict) -> Tuple[Optional[str], int, int, int, int]:
    """
    Return (model, input_tokens, output_tokens, cache_read, cache_write).
    Handles OpenAI-style, Anthropic-style, Gemini-style, and Cohere-style
    bodies. Zeros for anything missing.
    """
    if not isinstance(body, dict):
        return (None, 0, 0, 0, 0)

    model = body.get("model") or body.get("modelId")

    # OpenAI-style: body["usage"] = {prompt_tokens, completion_tokens, ...}
    u = body.get("usage") or {}
    if "prompt_tokens" in u or "completion_tokens" in u:
        input_t = int(u.get("prompt_tokens", 0))
        output_t = int(u.get("completion_tokens", 0))
        cache_r = int((u.get("prompt_tokens_details") or {}).get("cached_tokens", 0))
        return (model, input_t, output_t, cache_r, 0)

    # Anthropic-style: usage = {input_tokens, output_tokens, ...}
    if "input_tokens" in u or "output_tokens" in u:
        input_t = int(u.get("input_tokens", 0))
        output_t = int(u.get("output_tokens", 0))
        cache_r = int(u.get("cache_read_input_tokens", 0))
        cache_w = int(u.get("cache_creation_input_tokens", 0))
        return (model, input_t, output_t, cache_r, cache_w)

    # Gemini-style: body["usageMetadata"]
    um = body.get("usageMetadata") or body.get("usage_metadata") or {}
    if um:
        input_t = int(um.get("promptTokenCount", um.get("prompt_token_count", 0)))
        output_t = int(um.get("candidatesTokenCount", um.get("candidates_token_count", 0)))
        cache_r = int(um.get("cachedContentTokenCount", um.get("cached_content_token_count", 0)))
        return (model, input_t, output_t, cache_r, 0)

    # Cohere v2: body["meta"]["billed_units"] or body["meta"]["tokens"]
    meta = body.get("meta") or {}
    units = meta.get("billed_units") or meta.get("tokens") or {}
    if units:
        input_t = int(units.get("input_tokens", units.get("input", 0)))
        output_t = int(units.get("output_tokens", units.get("output", 0)))
        return (model, input_t, output_t, 0, 0)

    return (model, 0, 0, 0, 0)


def log_usage_from_body(provider: str, body: dict) -> bool:
    """
    Price a parsed response body and append a usage row. Returns True if a
    priceable LLM call was logged. Pure + synchronous — unit-testable.
    """
    model, inp, out, cr, cw = _extract_model_and_usage(provider, body)
    if not model or (inp == 0 and out == 0):
        # Not a priceable LLM call (could be list_models, a health check, etc.)
        return False
    price = _pricing.get_price(model)
    if price and price.unit == "token":
        cost_in = (inp / 1_000_000) * price.input_per_1m
        cost_out = (out / 1_000_000) * price.output_per_1m
        cost_total = cost_in + cost_out
    else:
        cost_in = cost_out = cost_total = 0.0
    usage_log.append_usage({
        "source": f"http-capture/{provider}",
        "model": model,
        "provider": provider,
        "input_tokens": inp,
        "output_tokens": out,
        "cache_read_tokens": cr,
        "cache_write_tokens": cw,
        "cost_input": cost_in,
        "cost_output": cost_out,
        "cost_total": cost_total,
        "session_id": None,
        "extra": {"via": "httpx_transport"},
    })
    return True


def _parse_and_log(provider: str, content_encoding: str, raw: bytes) -> bool:
    """Decode + JSON-parse buffered bytes, then log. Best-effort; never raises."""
    try:
        if not raw or len(raw) > _MAX_BUFFER:
            return False
        decoded = _decode_body(content_encoding, raw)
        if decoded is None:
            return False
        body = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, AttributeError):
        return False
    try:
        return log_usage_from_body(provider, body)
    except Exception:  # noqa: BLE001 — telemetry must never break the caller
        return False


_INSTALLED = False


def _wrap_response(httpx_mod, response, request) -> None:
    """Attach a teeing stream to `response` if it's a priceable LLM JSON call."""
    host = urlsplit(str(request.url)).netloc
    provider = _classify_host(host)
    if provider is None:
        return
    content_type = (response.headers.get("content-type") or "").lower()

    if "text/event-stream" in content_type:
        _report_stream_gap(provider, str(request.url))
        return
    if "application/json" not in content_type:
        return

    content_encoding = response.headers.get("content-encoding") or ""
    inner = getattr(response, "stream", None)
    if inner is None:
        return

    is_async = hasattr(inner, "__aiter__")
    buf = bytearray()
    done = {"v": False}

    def finish():
        if done["v"]:
            return
        done["v"] = True
        _parse_and_log(provider, content_encoding, bytes(buf))

    if is_async:
        class _Tee(httpx_mod.AsyncByteStream):
            async def __aiter__(self):
                async for chunk in inner:
                    if len(buf) <= _MAX_BUFFER:
                        buf.extend(chunk)
                    yield chunk
                finish()

            async def aclose(self):
                try:
                    if hasattr(inner, "aclose"):
                        await inner.aclose()
                finally:
                    finish()
    else:
        class _Tee(httpx_mod.SyncByteStream):
            def __iter__(self):
                for chunk in inner:
                    if len(buf) <= _MAX_BUFFER:
                        buf.extend(chunk)
                    yield chunk
                finish()

            def close(self):
                try:
                    if hasattr(inner, "close"):
                        inner.close()
                finally:
                    finish()

    response.stream = _Tee()


def install_global_capture() -> bool:
    """
    Monkey-patch httpx transports so every request to a known LLM host gets
    its response stream tee'd and usage logged. Returns True if installed,
    False if httpx isn't available. Idempotent.
    """
    global _INSTALLED
    if _INSTALLED:
        return True
    try:
        import httpx
    except ImportError:
        return False

    original_sync = httpx.HTTPTransport.handle_request

    def sync_wrapped(self, request):
        response = original_sync(self, request)
        try:
            _wrap_response(httpx, response, request)
        except Exception:  # noqa: BLE001
            pass
        return response

    httpx.HTTPTransport.handle_request = sync_wrapped

    if hasattr(httpx, "AsyncHTTPTransport"):
        original_async = httpx.AsyncHTTPTransport.handle_async_request

        async def async_wrapped(self, request):
            response = await original_async(self, request)
            try:
                _wrap_response(httpx, response, request)
            except Exception:  # noqa: BLE001
                pass
            return response

        httpx.AsyncHTTPTransport.handle_async_request = async_wrapped

    _INSTALLED = True
    return True


def _report_stream_gap(provider: str, url: str) -> None:
    """Emit a single errors.jsonl entry noting a streaming call we couldn't price."""
    try:
        from errors import log_error
        log_error("http_capture", f"skipped stream: provider={provider} url={url}",
                  hint="Use track_openai / track_anthropic for streaming coverage.")
    except Exception:
        pass


if __name__ == "__main__":
    installed = install_global_capture()
    print("http capture installed." if installed else "httpx not available.")
