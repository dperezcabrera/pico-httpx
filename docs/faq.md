# FAQ

## How do I send headers or auth?

Not declaratively yet — that is deliberate scope control for 0.1. Pre-seed the instance client with your own `httpx.Client(headers=..., auth=...)`, or open an issue with your use case.

## Why does my stub return a dict and not a typed model?

0.1 returns `response.json()`. Validate at the edge with pico-pydantic (`@validate` on the consuming service method) or construct the model from the dict. Direct model returns are a candidate for a later release.

## Can I mix sync and async methods in one client?

Yes. Sync stubs use a shared `httpx.Client`, async stubs a shared `httpx.AsyncClient`; they coexist on the same class.

## How does this compose with retries and circuit breakers?

The client never retries by itself: a timeout or a refused connection reaches the caller after one attempt, as the httpx exception. Stack pico-resilience decorators on the same stub, `@retryable` on top:

```python
@retryable(max_attempts=3, retry_on=(httpx.HTTPError,))
@get("/users/{user_id}")
def get_user(self, user_id: int) -> dict: ...
```

A transient timeout or connection error is then retried and the caller only sees the successful result. When every attempt fails, the caller gets `pico_resilience.RetryExhaustedError`, with the last httpx exception in `last_error`.

`httpx.HTTPError` also covers non-2xx responses. For calls that are not safe to repeat (a `POST` that creates something), retry only failures where the request may not have been processed, and let a rejection through:

```python
@retryable(max_attempts=3, retry_on=(httpx.TransportError,))
@post("/orders")
def place_order(self, json: dict) -> dict: ...
```

Even then, a `ReadTimeout` can hit after the server processed the request: retry non-idempotent calls only when the API deduplicates them (an idempotency key, for example).
