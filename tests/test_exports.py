"""The public API is exactly what ``__all__`` declares (stability contract)."""

import pico_httpx


def test_public_api_is_declared_and_importable():
    assert set(pico_httpx.__all__) == {"HttpSettings", "delete", "get", "http_client", "patch", "post", "put"}
    for name in pico_httpx.__all__:
        assert getattr(pico_httpx, name) is not None
