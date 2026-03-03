"""
HTTP plugin for Catalyst.

Provides async HTTP GET/POST methods using urllib (stdlib only).
"""

import asyncio
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Any, Dict, Optional

from core.plugin import Plugin


class HttpPlugin(Plugin):
    name = "http"
    description = "Perform HTTP requests (GET, POST, etc.) using standard library"

    async def execute(
        self,
        method: str = 'GET',
        url: str = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Any:
        """
        Execute an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Target URL (required)
            headers: Optional dict of request headers
            data: Optional form data (dict) to be URL-encoded as application/x-www-form-urlencoded
            json_data: Optional JSON body (dict) - will be serialized and set Content-Type automatically
            timeout: Timeout in seconds (default 30)

        Returns:
            Response body parsed as JSON if Content-Type is JSON, otherwise decoded text.
        """
        if url is None:
            raise ValueError("url parameter is required for http plugin")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sync_request(method, url, headers, data, json_data, timeout)
        )

    def _sync_request(self, method, url, headers, data, json_data, timeout):
        # Prepare headers
        req_headers = headers.copy() if headers else {}
        body = None

        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            req_headers.setdefault('Content-Type', 'application/json')
        elif data is not None:
            # application/x-www-form-urlencoded
            import urllib.parse
            body = urllib.parse.urlencode(data).encode('utf-8')
            req_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')

        req = Request(url, headers=req_headers, method=method.upper())
        try:
            with urlopen(req, timeout=timeout, data=body) as resp:
                content_type = resp.headers.get('Content-Type', '')
                charset = 'utf-8'
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[1].split(';')[0].strip()
                raw = resp.read()
                # Try JSON first
                try:
                    return json.loads(raw.decode(charset))
                except Exception:
                    try:
                        return raw.decode(charset)
                    except Exception:
                        return raw
        except HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
            except Exception:
                err_body = str(e)
            raise RuntimeError(f"HTTP {e.code} error: {err_body}") from e
        except URLError as e:
            raise RuntimeError(f"URL error: {e.reason}") from e
        except Exception as e:
            raise
