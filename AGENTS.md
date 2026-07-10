# pico-httpx

Declarative HTTP clients: @http_client classes with @get/@post/... stubs; implementation generated at decoration time.

## Commands

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest --cov=pico_httpx --cov-report=term-missing tests/
mkdocs serve -f mkdocs.yml
```

## Project Structure

```
src/pico_httpx/
  __init__.py       # Public API
  client.py         # http_client + verb decorators, binding, shared clients, cleanup
  config.py         # HttpSettings (prefix "http", clients map)
```

## Key Concepts

- NO interceptors: the verb decorator REPLACES the stub at decoration time -> pico-resilience stacks on top naturally.
- Binding: {placeholders} by param name; `json` param = body; the rest = query params (None dropped).
- Return annotation httpx.Response = raw; anything else = response.json() (None on empty body). Non-2xx raises HTTPStatusError.
- Sync stubs share httpx.Client, async stubs httpx.AsyncClient (lazy, closed on shutdown; running-loop aware).
- base_url: literal on decorator wins; else http.clients.<name>.base_url at FIRST request.
- Custom __init__ must store settings as self._pico_httpx_settings.

## Boundaries

- No headers/auth DSL, no typed model returns (0.1 scope, documented)
- Config dict fields need parameterized annotations (dict[str, Any], never bare dict)
- Do not modify `_version.py`
