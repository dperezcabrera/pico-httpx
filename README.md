# pico-httpx

[![PyPI version](https://img.shields.io/pypi/v/pico-httpx.svg)](https://pypi.org/project/pico-httpx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/dperezcabrera/pico-httpx/actions/workflows/ci.yml/badge.svg)](https://github.com/dperezcabrera/pico-httpx/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-httpx/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-httpx)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://dperezcabrera.github.io/pico-httpx/)

Declarative HTTP clients for the [pico ecosystem](https://github.com/dperezcabrera/pico-ioc): write the interface, get the implementation. Powered by httpx.

## Installation

```bash
pip install pico-httpx
```

## Quick start

```python
import httpx
from pico_httpx import http_client, get, post

@http_client(base_url="https://api.example.com")   # or resolve from config, see below
class UsersApi:
    @get("/users/{user_id}")
    def get_user(self, user_id: int, verbose: bool | None = None) -> dict: ...

    @post("/users")
    async def create_user(self, json: dict) -> dict: ...

    @get("/users/{user_id}/avatar")
    def avatar(self, user_id: int) -> httpx.Response: ...
```

The class is a regular `@component` — inject it anywhere. Rules:

- `{placeholders}` in the path bind to method parameters.
- A parameter named `json` is the request body.
- Every other parameter becomes a query param (`None` values are dropped).
- Return annotation `httpx.Response` gets the raw response; anything else gets `response.json()` (or `None` on an empty body). Non-2xx raises `httpx.HTTPStatusError`.
- Sync stubs share an `httpx.Client`, async stubs an `httpx.AsyncClient`; both close on container shutdown.

Base URL from config instead of code:

```yaml
http:
  timeout_seconds: 10
  clients:
    users:
      base_url: https://users.internal
```

```python
@http_client(name="users")
class UsersApi: ...
```

Compose with the rest of the ecosystem: stack `@retryable` / `@circuit_breaker` (pico-resilience) on the same methods, and pico-otel traces the underlying httpx calls.

## Documentation

Full documentation: https://dperezcabrera.github.io/pico-httpx/

## License

MIT
