# FAQ

## How do I send headers or auth?

Not declaratively yet — that is deliberate scope control for 0.1. Pre-seed the instance client with your own `httpx.Client(headers=..., auth=...)`, or open an issue with your use case.

## Why does my stub return a dict and not a typed model?

0.1 returns `response.json()`. Validate at the edge with pico-pydantic (`@validate` on the consuming service method) or construct the model from the dict. Direct model returns are a candidate for a later release.

## Can I mix sync and async methods in one client?

Yes. Sync stubs use a shared `httpx.Client`, async stubs a shared `httpx.AsyncClient`; they coexist on the same class.

## How does this compose with retries and circuit breakers?

Stack pico-resilience decorators on the same stub — `@retryable` on top:

```python
@retryable(max_attempts=3, retry_on=(httpx.HTTPError,))
@get("/users/{user_id}")
def get_user(self, user_id: int) -> dict: ...
```
