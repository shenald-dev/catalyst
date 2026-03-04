"""
HTTP plugin for Catalyst.

Provides async HTTP requests using aiohttp with connection pooling, retries, and circuit breaker.
Falls back to urllib if aiohttp is not installed.
"""

import asyncio
import json
from typing import Any, Dict, Optional

from core.plugin import Plugin


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self.last_failure_time and (asyncio.get_event_loop().time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker is OPEN due to repeated failures")
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            if self.state == "CLOSED":
                self.failure_count += 1
                self.last_failure_time = asyncio.get_event_loop().time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
            elif self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.last_failure_time = asyncio.get_event_loop().time()
            raise e


class HttpPlugin(Plugin):
    name = "http"
    description = "Perform HTTP requests with aiohttp (connection pooling, retries, circuit breaker)"

    def __init__(self, retry_policy: Optional[Dict] = None, circuit_breaker: Optional[Dict] = None):
        """
        Initialize HTTP plugin.

        Args:
            retry_policy: Dict with keys: max_attempts (int, default 3), backoff_factor (float, default 0.5), status_forcelist (list of int, default [500,502,503,504])
            circuit_breaker: Dict with keys: failure_threshold, recovery_timeout
        """
        super().__init__()
        self.retry_policy = retry_policy or {"max_attempts": 3, "backoff_factor": 0.5, "status_forcelist": [500, 502, 503, 504]}
        self.cb_config = circuit_breaker or {"failure_threshold": 5, "recovery_timeout": 60.0}
        self._session = None
        self._circuit_breaker = None
        self._using_aiohttp = False

    def on_load(self):
        """Check if aiohttp is available and initialize session and circuit breaker."""
        try:
            import aiohttp
            self._using_aiohttp = True
            self._session = aiohttp.ClientSession()
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=self.cb_config["failure_threshold"],
                recovery_timeout=self.cb_config["recovery_timeout"]
            )
        except ImportError:
            self._using_aiohttp = False
            import warnings
            warnings.warn("aiohttp not installed; HTTP plugin will use blocking urllib fallback", RuntimeWarning)

    async def on_unload(self):
        """Close aiohttp session if used."""
        if self._session is not None:
            await self._session.close()

    def health_check(self) -> bool:
        """Health check: if using aiohttp, session should be open."""
        if self._using_aiohttp:
            return self._session is not None and not self._session.closed
        return True  # fallback always healthy

    async def execute(
        self,
        method: str = 'GET',
        url: str = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30,
        retry_policy: Optional[Dict] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Execute an HTTP request with retry and circuit breaker.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Target URL (required)
            headers: Optional dict of request headers
            data: Form data (application/x-www-form-urlencoded)
            json_data: JSON body (auto-sets Content-Type)
            timeout: Timeout in seconds (default 30)
            retry_policy: Override plugin's default retry policy for this request.
            raise_for_status: If True, raise for 4xx/5xx responses (after retries).

        Returns:
            Response body parsed as JSON if Content-Type is JSON, otherwise text.
        """
        if url is None:
            raise ValueError("url parameter is required for http plugin")

        # Merge retry policy
        policy = {**self.retry_policy, **(retry_policy or {})}
        max_attempts = policy.get("max_attempts", 3)
        backoff_factor = policy.get("backoff_factor", 0.5)
        status_forcelist = policy.get("status_forcelist", [500, 502, 503, 504])

        if self._using_aiohttp:
            return await self._aiohttp_request(method, url, headers, data, json_data, timeout, max_attempts, backoff_factor, status_forcelist, raise_for_status)
        else:
            return await self._fallback_request(method, url, headers, data, json_data, timeout, max_attempts, backoff_factor, status_forcelist, raise_for_status)

    async def _aiohttp_request(self, method, url, headers, data, json_data, timeout, max_attempts, backoff_factor, status_forcelist, raise_for_status):
        """Execute using aiohttp with retry and circuit breaker."""
        import aiohttp
        attempt = 0
        last_exception = None
        while attempt < max_attempts:
            attempt += 1
            try:
                # Use circuit breaker to protect against repeated failures
                async def do_request():
                    req_headers = headers.copy() if headers else {}
                    req_kwargs = {"headers": req_headers, "timeout": aiohttp.ClientTimeout(total=timeout)}
                    if json_data is not None:
                        req_kwargs["json"] = json_data
                    elif data is not None:
                        req_kwargs["data"] = data
                    async with self._session.request(method.upper(), url, **req_kwargs) as resp:
                        if raise_for_status and resp.status >= 400:
                            # If status in forcelist and we have retries left, treat as retryable
                            if resp.status in status_forcelist and attempt < max_attempts:
                                resp.raise_for_status()  # will raise aiohttp.ClientResponseError
                            else:
                                resp.raise_for_status()
                        content_type = resp.headers.get('Content-Type', '')
                        text = await resp.text()
                        if 'application/json' in content_type:
                            return json.loads(text)
                        return text
                # Wrap with circuit breaker
                result = await self._circuit_breaker.call(do_request)
                return result
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < max_attempts:
                    await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
                continue
            except Exception as e:
                # Non-retryable errors (like invalid URL) propagate immediately
                raise e
        # Exhausted retries
        raise RuntimeError(f"HTTP request failed after {max_attempts} attempts") from last_exception

    async def _fallback_request(self, method, url, headers, data, json_data, timeout, max_attempts, backoff_factor, status_forcelist, raise_for_status):
        """Fallback to urllib in executor with retry."""
        loop = asyncio.get_event_loop()
        attempt = 0
        last_exception = None
        while attempt < max_attempts:
            attempt += 1
            try:
                return await loop.run_in_executor(
                    None,
                    lambda: self._sync_fallback(method, url, headers, data, json_data, timeout, raise_for_status)
                )
            except Exception as e:
                last_exception = e
                # Determine if retryable
                if isinstance(e, RuntimeError) and hasattr(e, '__cause__') and isinstance(e.__cause__, TimeoutError):
                    # Timeout is retryable
                    pass
                elif isinstance(e, RuntimeError) and "HTTP" in str(e):
                    # Check status code if available; parse from message maybe?
                    # Hard to parse, but we can treat all RuntimeErrors as possibly retryable?
                    # Simpler: retry on any exception except for URLError with non-retryable reason?
                    pass
                else:
                    # Non-retryable
                    raise
                if attempt < max_attempts:
                    await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
                continue
        raise RuntimeError(f"HTTP request failed after {max_attempts} attempts") from last_exception

    def _sync_fallback(self, method, url, headers, data, json_data, timeout, raise_for_status):
        from urllib.request import Request, urlopen
        from urllib.error import URLError, HTTPError
        import json
        req_headers = headers.copy() if headers else {}
        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            req_headers.setdefault('Content-Type', 'application/json')
        elif data is not None:
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
            if raise_for_status:
                raise RuntimeError(f"HTTP {e.code} error: {err_body}") from e
            else:
                # Return error response as text
                return err_body
        except URLError as e:
            raise RuntimeError(f"URL error: {e.reason}") from e
        except Exception as e:
            raise
