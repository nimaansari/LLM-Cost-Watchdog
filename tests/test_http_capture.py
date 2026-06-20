#!/usr/bin/env python3
"""
Tests for the httpx-transport capture path.

These verify the fix for the bug where the old implementation read
`response.content` at the transport layer (where it isn't populated yet) and
therefore captured nothing for normal non-streaming calls. The tee approach
must (a) still hand the SDK its untouched body and (b) actually log usage.
"""
import gzip
import json
import os
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
os.environ["CW_STATIC_ONLY"] = "1"

import http_capture  # noqa: E402

try:
    import httpx
    HAVE_HTTPX = True
except ImportError:
    HAVE_HTTPX = False


def _make_response(body: dict, *, encoding: str = "identity", url="https://api.openai.com/v1/chat/completions"):
    payload = json.dumps(body).encode("utf-8")
    if encoding == "gzip":
        payload = gzip.compress(payload)
    headers = {"content-type": "application/json"}
    if encoding != "identity":
        headers["content-encoding"] = encoding

    class _Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield payload

        def close(self):
            pass

    req = httpx.Request("POST", url)
    resp = httpx.Response(200, headers=headers, stream=_Stream(), request=req)
    return resp, req


@unittest.skipUnless(HAVE_HTTPX, "httpx not installed")
class TestHttpCapture(unittest.TestCase):
    def setUp(self):
        self._logged = []
        self._orig = http_capture.usage_log.append_usage
        http_capture.usage_log.append_usage = lambda row: self._logged.append(row)

    def tearDown(self):
        http_capture.usage_log.append_usage = self._orig

    def test_openai_json_is_captured_and_passed_through(self):
        body = {"model": "gpt-4o", "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
        resp, req = _make_response(body)
        http_capture._wrap_response(httpx, resp, req)
        resp.read()  # the SDK reads the body
        self.assertEqual(resp.json(), body)            # passthrough intact
        self.assertEqual(len(self._logged), 1)         # usage captured
        self.assertEqual(self._logged[0]["model"], "gpt-4o")
        self.assertEqual(self._logged[0]["input_tokens"], 100)
        self.assertEqual(self._logged[0]["output_tokens"], 50)

    def test_gzip_body_is_decoded(self):
        body = {"model": "claude-sonnet-4-6",
                "usage": {"input_tokens": 200, "output_tokens": 80}}
        resp, req = _make_response(body, encoding="gzip",
                                   url="https://api.anthropic.com/v1/messages")
        http_capture._wrap_response(httpx, resp, req)
        resp.read()
        self.assertEqual(resp.json(), body)            # SDK still decodes fine
        self.assertEqual(len(self._logged), 1)
        self.assertEqual(self._logged[0]["input_tokens"], 200)
        self.assertEqual(self._logged[0]["provider"], "anthropic")

    def test_non_priceable_call_not_logged(self):
        # e.g. a list-models response: no usage block.
        body = {"data": [{"id": "gpt-4o"}], "object": "list"}
        resp, req = _make_response(body)
        http_capture._wrap_response(httpx, resp, req)
        resp.read()
        self.assertEqual(resp.json(), body)
        self.assertEqual(self._logged, [])

    def test_unknown_host_ignored(self):
        body = {"model": "gpt-4o", "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        resp, req = _make_response(body, url="https://example.com/v1/chat")
        http_capture._wrap_response(httpx, resp, req)
        resp.read()
        self.assertEqual(self._logged, [])             # not a known LLM host

    def test_log_usage_from_body_pure(self):
        # Pure function, no httpx needed for the parsing logic itself.
        ok = http_capture.log_usage_from_body(
            "google",
            {"model": "gemini-2.5-flash",
             "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 7}},
        )
        self.assertTrue(ok)
        self.assertEqual(self._logged[0]["output_tokens"], 7)


if __name__ == "__main__":
    unittest.main()
