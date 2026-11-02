from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any

import requests

from src.parsing import loads_payload

RETRYABLE = {429, 500, 502, 503}


class ApiError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:500]}")
        self.status = status


class ApiClient:
    """GET client with backoff on 429 and transient 5xx. 400 and 401 fail immediately."""

    def __init__(
        self,
        base_url: str,
        token: str,
        session: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 6,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept-Encoding": "gzip",
            }
        )
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.retries = 0

    def get_json(
        self, path: str, params: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        url = f"{self.base_url}{path}"
        delay = 1.0
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                response = self.session.get(url, params=params, timeout=90)
            except requests.RequestException as exc:
                last_error = exc
                if attempt == self.max_attempts - 1:
                    raise
                self.retries += 1
                self.sleep(delay + random.random())
                delay = min(delay * 2, 30)
                continue
            if response.status_code in RETRYABLE:
                if attempt == self.max_attempts - 1:
                    raise ApiError(response.status_code, response.text)
                self.retries += 1
                retry_after = response.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else delay + random.random()
                except ValueError:
                    wait = delay + random.random()
                self.sleep(wait)
                delay = min(delay * 2, 30)
                continue
            if response.status_code >= 400:
                raise ApiError(response.status_code, response.text)
            payload = loads_payload(response.text) if response.text else None
            return payload, dict(response.headers)
        if last_error:
            raise last_error
        raise ApiError(0, "request failed without a response")
