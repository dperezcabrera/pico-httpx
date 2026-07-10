"""Declarative HTTP clients: ``@http_client`` classes with ``@get``/``@post``/
``@put``/``@delete``/``@patch`` stub methods.

The decorator generates the implementation: path placeholders bind to the
method's parameters, a parameter named ``json`` becomes the request body,
every other bound parameter becomes a query param (``None`` values are
dropped). Sync stubs use a shared ``httpx.Client``; async stubs a shared
``httpx.AsyncClient``. Both close on container shutdown.
"""

import functools
import inspect
import string
from typing import Any

import httpx
from pico_ioc import cleanup, component

from .config import HttpSettings

HTTP_CLIENT_META = "_pico_httpx_meta"
_BODY_PARAM = "json"


def _new_sync_client(base_url: str, timeout: float) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=timeout)


def _new_async_client(base_url: str, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)


def http_client(_cls=None, *, base_url: str = "", name: str = ""):
    """Turn a class of request stubs into an injectable HTTP client component.

    ``base_url`` is either given literally or resolved from config at
    first request: ``http.clients.<name>.base_url`` (``name`` defaults
    to the class name).
    """

    def dec(cls):
        setattr(cls, HTTP_CLIENT_META, {"base_url": base_url, "name": name or cls.__name__})
        if "__init__" not in cls.__dict__:
            cls.__init__ = _make_init()
        cls._pico_httpx_close = cleanup(_close_clients)
        return component(cls)

    return dec(_cls) if _cls is not None else dec


def _make_init():
    def __init__(self, settings: HttpSettings):
        self._pico_httpx_settings = settings

    return __init__


def _close_clients(self) -> None:
    sync_client = self.__dict__.pop("_pico_httpx_client", None)
    if sync_client is not None:
        sync_client.close()
    async_client = self.__dict__.pop("_pico_httpx_aclient", None)
    if async_client is not None:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(async_client.aclose())
        else:
            # Sync shutdown inside a running loop: schedule the close on it.
            loop.create_task(async_client.aclose())


def _settings_of(instance) -> HttpSettings:
    settings = getattr(instance, "_pico_httpx_settings", None)
    if settings is None:
        raise RuntimeError(
            f"{type(instance).__name__} defines __init__ but did not store the injected "
            "HttpSettings as self._pico_httpx_settings"
        )
    return settings


def _base_url_of(instance) -> str:
    meta = getattr(type(instance), HTTP_CLIENT_META)
    if meta["base_url"]:
        return meta["base_url"]
    from_config = _settings_of(instance).clients.get(meta["name"], {}).get("base_url", "")
    if not from_config:
        raise RuntimeError(
            f"no base_url for HTTP client {meta['name']!r}: pass base_url= to @http_client "
            f"or set http.clients.{meta['name']}.base_url in config"
        )
    return from_config


def _sync_client_of(instance) -> httpx.Client:
    client = instance.__dict__.get("_pico_httpx_client")
    if client is None:
        client = _new_sync_client(_base_url_of(instance), _settings_of(instance).timeout_seconds)
        instance.__dict__["_pico_httpx_client"] = client
    return client


def _async_client_of(instance) -> httpx.AsyncClient:
    client = instance.__dict__.get("_pico_httpx_aclient")
    if client is None:
        client = _new_async_client(_base_url_of(instance), _settings_of(instance).timeout_seconds)
        instance.__dict__["_pico_httpx_aclient"] = client
    return client


def _bind(sig: inspect.Signature, path: str, args, kwargs):
    bound = sig.bind(None, *args, **kwargs)  # None stands in for self
    bound.apply_defaults()
    arguments = dict(list(bound.arguments.items())[1:])

    placeholders = {name for _, name, _, _ in string.Formatter().parse(path) if name}
    missing = placeholders - arguments.keys()
    if missing:
        raise TypeError(f"path {path!r} needs parameters {sorted(missing)}")

    url = path.format(**{k: arguments[k] for k in placeholders})
    body = arguments.pop(_BODY_PARAM, None)
    params = {k: v for k, v in arguments.items() if k not in placeholders and v is not None}
    return url, params, body


def _convert(response: httpx.Response, annotation: Any):
    if annotation is httpx.Response:
        return response
    if not response.content:
        return None
    return response.json()


def _request(method: str, path: str):
    def dec(fn):
        sig = inspect.signature(fn)

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_impl(self, *args, **kwargs):
                url, params, body = _bind(sig, path, args, kwargs)
                response = await _async_client_of(self).request(method, url, params=params, json=body)
                response.raise_for_status()
                return _convert(response, sig.return_annotation)

            return async_impl

        @functools.wraps(fn)
        def sync_impl(self, *args, **kwargs):
            url, params, body = _bind(sig, path, args, kwargs)
            response = _sync_client_of(self).request(method, url, params=params, json=body)
            response.raise_for_status()
            return _convert(response, sig.return_annotation)

        return sync_impl

    return dec


def get(path: str):
    return _request("GET", path)


def post(path: str):
    return _request("POST", path)


def put(path: str):
    return _request("PUT", path)


def delete(path: str):
    return _request("DELETE", path)


def patch(path: str):
    return _request("PATCH", path)
