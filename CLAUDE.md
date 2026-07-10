Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-httpx — Declarative HTTP clients: @http_client classes with @get/@post/... stubs; implementation generated at decoration time. Auto-discovered via the `pico_boot.modules` entry point. See it wired with the whole ecosystem in the flagship use case (pico-boot docs).

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`; httpx `>= 0.28`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`.
- requires-python >= 3.11
- Commit messages: one line only
