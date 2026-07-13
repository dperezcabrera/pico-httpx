# pico-httpx

[![PyPI](https://img.shields.io/pypi/v/pico-httpx.svg)](https://pypi.org/project/pico-httpx/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-httpx)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-httpx/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-httpx/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-httpx)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-httpx&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-httpx)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-httpx&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-httpx)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-httpx&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-httpx)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pico-httpx)](https://pypi.org/project/pico-httpx/)
[![Docs](https://img.shields.io/badge/Docs-pico--httpx-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-httpx/)
[![Interactive Lab](https://img.shields.io/badge/Learn-online-green?style=flat&logo=python&logoColor=white)](https://dperezcabrera.github.io/pico-learn/)

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

## Built for AI-assisted development

pico-httpx is part of an ecosystem designed for humans and coding agents building software together. Every package ships `AGENTS.md` working conventions, an `llms.txt` machine-readable docs index and documented behaviour pinned by regression tests; [pico-testing](https://github.com/dperezcabrera/pico-testing) gives agents a verification loop for their own changes, and releases are gated by the whole ecosystem booting together against real infrastructure. The full story: [Built for AI-assisted development](https://github.com/dperezcabrera/pico-ioc#built-for-ai-assisted-development).

Install the agent skills for [Claude Code](https://code.claude.com) or [OpenAI Codex](https://openai.com/index/introducing-codex/):

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

The `pico-conventions` skill teaches the assistant this module's API surface and invariants; `/add-component` and `/add-tests` scaffold components and tests that use it.

## License

MIT
