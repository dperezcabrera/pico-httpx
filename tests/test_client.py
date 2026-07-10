import json
import sys

import httpx
import pytest

from pico_httpx import HttpSettings, delete, get, http_client, post


@http_client(base_url="https://api.test")
class EchoApi:
    @get("/items/{item_id}")
    def get_item(self, item_id: int, verbose: bool | None = None) -> dict: ...

    @post("/items")
    def create_item(self, json: dict) -> dict: ...

    @delete("/items/{item_id}")
    def remove_item(self, item_id: int) -> httpx.Response: ...

    @get("/empty")
    def empty(self) -> None: ...

    @get("/missing")
    def missing(self) -> dict: ...

    @get("/items/{item_id}")
    async def get_item_async(self, item_id: int) -> dict: ...


@http_client(name="users")
class ConfiguredApi:
    @get("/ping")
    def ping(self) -> dict: ...


@http_client(name="orphan")
class UnconfiguredApi:
    @get("/ping")
    def ping(self) -> dict: ...


def _client(container, cls):
    return container.get(cls)


def test_path_params_and_query(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    data = api.get_item(7, verbose=True)
    assert data["method"] == "GET"
    assert data["path"] == "/items/7"
    assert data["query"] == {"verbose": "true"}


def test_none_query_params_are_dropped(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    assert api.get_item(7)["query"] == {}


def test_json_body_is_sent(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    data = api.create_item(json={"name": "thing"})
    assert data["method"] == "POST"
    assert json.loads(data["body"]) == {"name": "thing"}


def test_response_annotation_returns_raw_response(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    response = api.remove_item(3)
    assert isinstance(response, httpx.Response)
    assert response.status_code == 200


def test_empty_body_returns_none(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    assert api.empty() is None


def test_error_status_raises(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    with pytest.raises(httpx.HTTPStatusError):
        api.missing()


@pytest.mark.asyncio
async def test_async_stub_uses_async_client(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    data = await api.get_item_async(9)
    assert data["path"] == "/items/9"


def test_base_url_resolved_from_config(make_container, echo_transport):
    container = make_container(
        sys.modules[__name__],
        config={"http": {"clients": {"users": {"base_url": "https://users.test"}}}},
    )
    assert container.get(ConfiguredApi).ping()["path"] == "/ping"


def test_missing_base_url_raises(make_container, echo_transport):
    container = make_container(sys.modules[__name__])
    with pytest.raises(RuntimeError, match="no base_url"):
        container.get(UnconfiguredApi).ping()


def test_missing_path_param_raises(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    with pytest.raises(TypeError):
        api.get_item()


def test_clients_closed_on_shutdown(make_container, echo_transport):
    container = make_container(sys.modules[__name__])
    api = container.get(EchoApi)
    api.get_item(1)
    sync_client = api.__dict__["_pico_httpx_client"]
    container.shutdown()
    assert sync_client.is_closed
    assert "_pico_httpx_client" not in api.__dict__


@http_client(base_url="https://api.test")
class MoreVerbs:
    from pico_httpx import patch as patch_verb
    from pico_httpx import put as put_verb

    @put_verb("/items/{item_id}")
    def replace(self, item_id: int, json: dict) -> dict: ...

    @patch_verb("/items/{item_id}")
    def tweak(self, item_id: int, json: dict) -> dict: ...


def test_put_and_patch(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(MoreVerbs)
    assert api.replace(1, json={"a": 1})["method"] == "PUT"
    assert api.tweak(1, json={"a": 1})["method"] == "PATCH"


@http_client
class BareDecorator:
    @get("/ping")
    def ping(self) -> dict: ...


def test_http_client_without_parens_needs_config_by_class_name(make_container, echo_transport):
    container = make_container(
        sys.modules[__name__],
        config={"http": {"clients": {"BareDecorator": {"base_url": "https://bare.test"}}}},
    )
    assert container.get(BareDecorator).ping()["path"] == "/ping"


@http_client(base_url="https://api.test")
class CustomInit:
    def __init__(self, settings: HttpSettings):
        self._pico_httpx_settings = settings
        self.ready = True

    @get("/ping")
    def ping(self) -> dict: ...


@http_client(base_url="https://api.test")
class BrokenInit:
    def __init__(self, settings: HttpSettings):
        pass

    @get("/ping")
    def ping(self) -> dict: ...


def test_custom_init_is_preserved(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(CustomInit)
    assert api.ready is True
    assert api.ping()["path"] == "/ping"


def test_custom_init_without_settings_raises(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(BrokenInit)
    with pytest.raises(RuntimeError, match="_pico_httpx_settings"):
        api.ping()


def test_async_client_closed_on_sync_shutdown(make_container, echo_transport):
    import asyncio

    container = make_container(sys.modules[__name__])
    api = container.get(EchoApi)
    asyncio.run(api.get_item_async(1))
    aclient = api.__dict__["_pico_httpx_aclient"]
    container.shutdown()
    assert aclient.is_closed


@pytest.mark.asyncio
async def test_async_client_close_scheduled_on_running_loop(make_container, echo_transport):
    import asyncio

    container = make_container(sys.modules[__name__])
    api = container.get(EchoApi)
    await api.get_item_async(1)
    aclient = api.__dict__["_pico_httpx_aclient"]
    container.shutdown()
    for _ in range(5):
        await asyncio.sleep(0)
    assert aclient.is_closed


def test_real_client_factories():
    from pico_httpx.client import _new_async_client, _new_sync_client

    sync_client = _new_sync_client("https://x.test", 1.0)
    assert str(sync_client.base_url) == "https://x.test"
    sync_client.close()

    async_client = _new_async_client("https://x.test", 1.0)
    assert str(async_client.base_url) == "https://x.test"
    import asyncio

    asyncio.run(async_client.aclose())


@http_client(base_url="https://api.test")
class BadPath:
    @get("/things/{thing_id}")
    def broken(self) -> dict: ...


def test_placeholder_without_matching_param_raises(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(BadPath)
    with pytest.raises(TypeError, match="needs parameters"):
        api.broken()


@pytest.mark.asyncio
async def test_async_client_is_reused(make_container, echo_transport):
    api = make_container(sys.modules[__name__]).get(EchoApi)
    await api.get_item_async(1)
    first = api.__dict__["_pico_httpx_aclient"]
    await api.get_item_async(2)
    assert api.__dict__["_pico_httpx_aclient"] is first
