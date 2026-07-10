# Architecture

```
@http_client(base_url=|name=)          HttpSettings (@configured, prefix http)
        |                                        |
   class meta + generated __init__(settings) ----+
        |
@get/@post/... stub --- decoration time: generate impl from signature
        |
  per-instance lazy httpx.Client / AsyncClient (base_url, timeout)
        |
  _pico_httpx_close (@cleanup): both clients closed on container shutdown
```

## Design decisions

- **Implementation generated at decoration time**: each verb decorator
  inspects the stub's signature once and swaps in a sync or async
  implementation. No interceptors, no proxies — calling the method IS the
  request, so pico-resilience decorators stack on top naturally.
- **Binding rules are positional-free**: path `{placeholders}` are matched by
  parameter NAME; the parameter named `json` is the body; every other bound
  argument becomes a query param, with `None` dropped so optional filters
  need no special casing.
- **Two shared clients per instance**: sync stubs share one `httpx.Client`,
  async stubs one `httpx.AsyncClient` — connection pooling without global
  state. Both close via a `@cleanup` hook (running-loop aware: inside a loop
  the async close is scheduled, outside it runs via `asyncio.run`).
- **Config-or-literal base URL**: a literal on the decorator wins; otherwise
  `http.clients.<name>.base_url` resolves at FIRST request, so containers can
  build before config is complete. No base URL raises a clear RuntimeError.
- **Deliberate 0.1 scope**: no headers/auth DSL, no typed model returns —
  documented in the FAQ with escape hatches, added only on demand.
