# pico-httpx

Declarative HTTP clients: write the interface, get the implementation.

## Install

```bash
pip install pico-httpx
```

## 30-second example

```python
from pico_httpx import http_client, get

@http_client(base_url="https://api.example.com")
class UsersApi:
    @get("/users/{user_id}")
    def get_user(self, user_id: int) -> dict: ...
```

`UsersApi` is a regular pico component — inject it into services and call `get_user(7)`; the request, JSON parsing and error raising are generated for you.

**See it in context**: the [flagship use case](https://dperezcabrera.github.io/pico-boot/flagship/) wires this module into a full order platform together with the rest of the ecosystem.
