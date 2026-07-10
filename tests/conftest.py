import httpx
import pytest
from pico_ioc import DictSource, configuration, init

from pico_httpx import client as client_module


@pytest.fixture(autouse=True)
def isolate_from_installed_plugins(monkeypatch):
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")


@pytest.fixture
def make_container():
    created = []

    def _make(*modules, config=None):
        cfg = configuration(DictSource(config or {}))
        container = init(modules=["pico_httpx", *modules], config=cfg)
        created.append(container)
        return container

    yield _make
    for c in reversed(created):
        c.shutdown()


@pytest.fixture
def echo_transport(monkeypatch):
    """Routes every request to an in-memory echo handler; returns the request log."""
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/missing"):
            return httpx.Response(404, json={"detail": "not found"})
        if request.url.path.endswith("/empty"):
            return httpx.Response(204)
        return httpx.Response(
            200,
            json={
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.url.params),
                "body": request.content.decode() or None,
            },
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        client_module,
        "_new_sync_client",
        lambda base_url, timeout: httpx.Client(base_url=base_url, timeout=timeout, transport=transport),
    )
    monkeypatch.setattr(
        client_module,
        "_new_async_client",
        lambda base_url, timeout: httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport),
    )
    return requests
