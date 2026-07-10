"""Settings for pico-httpx (prefix ``http``, zero-config)."""

from dataclasses import dataclass, field
from typing import Any

from pico_ioc import configured


@configured(target="self", prefix="http", mapping="tree")
@dataclass
class HttpSettings:
    """``clients`` maps a client name to its settings, e.g.
    ``http.clients.users.base_url``. A literal ``base_url`` on the
    decorator wins over config."""

    timeout_seconds: float = 10.0
    # dict[str, Any] (not bare dict): the config builder only walks
    # parameterized mapping annotations.
    clients: dict[str, Any] = field(default_factory=dict)
