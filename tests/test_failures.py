"""Transport failures: the stub makes one attempt and lets httpx's exception
through unwrapped; retries come from stacking pico-resilience's @retryable."""

import sys

import httpx
import pytest
from pico_resilience import RetryExhaustedError, retryable

from pico_httpx import client as client_module
from pico_httpx import get, http_client, post


@http_client(base_url="https://api.test")
class FlakyApi:
    @get("/items/{item_id}")
    def get_item(self, item_id: int) -> dict: ...

    @get("/items/{item_id}")
    async def get_item_async(self, item_id: int) -> dict: ...

    @retryable(max_attempts=3, backoff_seconds=0, retry_on=(httpx.HTTPError,))
    @get("/items/{item_id}")
    def get_item_retried(self, item_id: int) -> dict: ...

    @retryable(max_attempts=3, backoff_seconds=0, retry_on=(httpx.HTTPError,))
    @get("/items/{item_id}")
    async def get_item_retried_async(self, item_id: int) -> dict: ...

    @retryable(max_attempts=3, backoff_seconds=0, retry_on=(httpx.TransportError,))
    @post("/orders")
    def place_order(self, json: dict) -> dict: ...


@pytest.fixture
def outcomes(monkeypatch):
    """Answers each request with the next queued outcome (an exception is raised
    as the transport failure); returns the queue and the request log."""
    queue: list = []
    requests: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        outcome = queue.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        client_module,
        "_new_sync_client",
        lambda base_url, timeout: httpx.Client(base_url=base_url, timeout=timeout, transport=transport),
    )
    monkeypatch.setattr(
        client_module,
        "_new_async_client",
        lambda base_url, timeout: httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport),
    )
    return queue, requests


def _api(make_container) -> FlakyApi:
    container = make_container("pico_resilience", sys.modules[__name__], config={"resilience": {"hot_reload": False}})
    return container.get(FlakyApi)


def _ok() -> httpx.Response:
    return httpx.Response(200, json={"ok": True})


@pytest.mark.parametrize(
    "failure",
    [httpx.ReadTimeout("read timed out"), httpx.ConnectTimeout("connect timed out"), httpx.ConnectError("refused")],
)
def test_transport_failure_reaches_the_caller_unwrapped_after_one_attempt(make_container, outcomes, failure):
    queue, requests = outcomes
    queue.append(failure)
    with pytest.raises(type(failure)) as raised:
        _api(make_container).get_item(1)
    assert raised.value is failure
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_async_transport_failure_reaches_the_caller_unwrapped(make_container, outcomes):
    queue, requests = outcomes
    queue.append(httpx.ReadTimeout("read timed out"))
    with pytest.raises(httpx.ReadTimeout):
        await _api(make_container).get_item_async(1)
    assert len(requests) == 1


def test_retryable_absorbs_transient_timeouts(make_container, outcomes):
    queue, requests = outcomes
    queue.extend([httpx.ConnectTimeout("connect timed out"), httpx.ReadTimeout("read timed out"), _ok()])
    assert _api(make_container).get_item_retried(1) == {"ok": True}
    assert len(requests) == 3


@pytest.mark.asyncio
async def test_retryable_absorbs_transient_timeouts_async(make_container, outcomes):
    queue, requests = outcomes
    queue.extend([httpx.ConnectError("refused"), _ok()])
    assert await _api(make_container).get_item_retried_async(1) == {"ok": True}
    assert len(requests) == 2


def test_exhausted_retries_raise_with_the_last_httpx_error(make_container, outcomes):
    queue, requests = outcomes
    last = httpx.ReadTimeout("read timed out")
    queue.extend([httpx.ConnectError("refused"), httpx.ConnectTimeout("connect timed out"), last])
    with pytest.raises(RetryExhaustedError) as raised:
        _api(make_container).get_item_retried(1)
    assert raised.value.last_error is last
    assert raised.value.attempts == 3 == len(requests)


def test_retry_narrowed_to_transport_errors_does_not_repeat_a_rejected_post(make_container, outcomes):
    queue, requests = outcomes
    queue.append(httpx.Response(409, json={"detail": "duplicate"}))
    with pytest.raises(httpx.HTTPStatusError):
        _api(make_container).place_order({"sku": "LATTE"})
    assert len(requests) == 1
