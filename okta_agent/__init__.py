"""CONCEPT:AU-ECO.messaging.native-backend-abstraction okta-agent: Okta Management API + MCP Server + A2A Server."""

import importlib
import inspect
from typing import Any

__version__ = "2.1.0"
__all__: list[str] = []

CORE_MODULES = [
    "okta_agent.okta_input_models",
    "okta_agent.okta_response_models",
    "okta_agent.api_client",
]
OPTIONAL_MODULES = {
    "okta_agent.agent_server": "agent",
    "okta_agent.mcp_server": "mcp",
}


def _expose_members(module):
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            if name not in __all__:
                __all__.append(name)


for module_name in CORE_MODULES:
    module = importlib.import_module(module_name)
    _expose_members(module)

_loaded_optional_modules: dict[str, Any] = {}


def _import_module_safely(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


_AVAILABILITY_FLAG_MARKERS = {
    "_MCP_AVAILABLE": "mcp_server",
    "_AGENT_AVAILABLE": "agent_server",
}
_NOT_AN_AVAILABILITY_FLAG = object()
_NAME_NOT_FOUND = object()


def _resolve_availability_flag(name: str) -> Any:
    """Return the live availability bool for a ``_*_AVAILABLE`` flag name.

    Returns ``_NOT_AN_AVAILABILITY_FLAG`` when ``name`` is not one of the
    recognized flags, so callers can distinguish "not a flag" from "flag
    resolved to False".
    """
    marker = _AVAILABILITY_FLAG_MARKERS.get(name)
    if marker is None:
        return _NOT_AN_AVAILABILITY_FLAG
    module_key = next((k for k in OPTIONAL_MODULES if marker in k), None)
    if module_key is None:
        return False
    return _import_module_safely(module_key) is not None


def _resolve_from_optional_modules(name: str) -> Any:
    """Lazily import each optional module and return its ``name`` attribute."""
    for module_name in OPTIONAL_MODULES:
        module = _loaded_optional_modules.get(module_name)
        if module is None:
            module = _import_module_safely(module_name)
            if module is not None:
                _loaded_optional_modules[module_name] = module
                _expose_members(module)
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    return _NAME_NOT_FOUND


def __getattr__(name: str) -> Any:
    flag = _resolve_availability_flag(name)
    if flag is not _NOT_AN_AVAILABILITY_FLAG:
        return flag

    value = _resolve_from_optional_modules(name)
    if value is not _NAME_NOT_FOUND:
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
