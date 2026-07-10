# Getting Started

## Prerequisites

- Python >= 3.11
- pico-ioc >= 2.2.0 (pico-boot recommended for auto-discovery)
- httpx >= 0.28 (installed automatically)

## Install

```bash
pip install pico-httpx
```

## Key concepts

| Piece | What it does |
|---|---|
| `@http_client(base_url=... \| name=...)` | Turns a class of stubs into an injectable component |
| `@get/@post/@put/@delete/@patch("/path/{param}")` | Generates the request implementation for a stub |
| `json` parameter | Sent as the JSON request body |
| Other parameters | Query params; `None` values are dropped |
| Return annotation | `httpx.Response` = raw response; anything else = `response.json()` (`None` on empty body) |

## Request semantics

- Non-2xx responses raise `httpx.HTTPStatusError` — pair with `@retryable` from pico-resilience for retries.
- Sync stubs share one `httpx.Client`; async stubs one `httpx.AsyncClient`. Both are created lazily on first request and closed on container shutdown.
- Timeout comes from `http.timeout_seconds` (default 10).

## Config-driven base URLs

```yaml
http:
  timeout_seconds: 5
  clients:
    users:
      base_url: https://users.internal
```

```python
@http_client(name="users")
class UsersApi: ...
```

A literal `base_url=` on the decorator always wins over config. With neither, the first request raises a clear `RuntimeError`.

## Custom __init__

If the class defines its own `__init__`, keep the injected settings visible to the generated methods:

```python
@http_client(name="users")
class UsersApi:
    def __init__(self, settings: HttpSettings, metrics: Metrics):
        self._pico_httpx_settings = settings
        self._metrics = metrics
```

## Testing your clients

Point the stubs at an `httpx.MockTransport` by pre-seeding the instance:

```python
api = container.get(UsersApi)
api._pico_httpx_client = httpx.Client(base_url="https://t", transport=httpx.MockTransport(handler))
```
