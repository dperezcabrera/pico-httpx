# Troubleshooting

## RuntimeError: no base_url for HTTP client

Pass `base_url=` to the decorator or set `http.clients.<name>.base_url` in
config; `name` defaults to the class name.

## RuntimeError: ... did not store the injected HttpSettings

Your class defines `__init__` — keep the generated methods working by storing
the settings: `self._pico_httpx_settings = settings`.

## TypeError: path '...' needs parameters

The path has a `{placeholder}` with no matching method parameter (or the call
omitted it). Names must match exactly.

## My query param is missing from the request

`None` values are dropped by design. Send an explicit value (`False`, `""`,
`0`) if the API needs the key present.

## httpx.HTTPStatusError bubbles out of my service

That is the contract: non-2xx raises. Catch it at the boundary, or stack
`@retryable(retry_on=(httpx.HTTPError,))` for transient failures.

## How do I point a client at a MockTransport in tests?

Pre-seed the instance before the first call:
`api._pico_httpx_client = httpx.Client(base_url=..., transport=httpx.MockTransport(handler))`.
