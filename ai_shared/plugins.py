"""
Plugin system — Dynamic loading, registration, and lifecycle for custom providers.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Type


# ── Plugin protocol ──────────────────────────────────────────────────────────

class PluginProtocol(Protocol):
    """Minimum interface every plugin must satisfy."""

    name: str

    def initialize(self, config: dict[str, Any]) -> None:
        ...

    def shutdown(self) -> None:
        ...


@dataclass
class PluginMetadata:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    category: str = "general"
    dependencies: list[str] = field(default_factory=list)


# ── Plugin Registry ──────────────────────────────────────────────────────────

class PluginRegistry:
    """Central registry for discovering, loading, and managing plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, _PluginEntry] = {}
        self._hooks: dict[str, list[Callable[..., Any]]] = {}

    # ── Registration ─────────────────────────────────────────────────────

    def register(
        self,
        plugin_class: type,
        *,
        metadata: PluginMetadata | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        meta = metadata or PluginMetadata(name=getattr(plugin_class, "name", plugin_class.__name__))
        instance = plugin_class()
        if hasattr(instance, "initialize"):
            instance.initialize(config or {})
        self._plugins[meta.name] = _PluginEntry(
            cls=plugin_class, instance=instance, metadata=meta, config=config or {}
        )

    def register_from_module(self, module_path: str, *, config: dict[str, Any] | None = None) -> None:
        """Dynamically import a module and register any PluginProtocol classes."""
        mod = importlib.import_module(module_path)
        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if hasattr(obj, "name") and hasattr(obj, "initialize"):
                self.register(obj, config=config)

    def unregister(self, name: str) -> bool:
        entry = self._plugins.pop(name, None)
        if entry is None:
            return False
        if hasattr(entry.instance, "shutdown"):
            entry.instance.shutdown()
        return True

    # ── Lookup ───────────────────────────────────────────────────────────

    def get(self, name: str) -> Any:
        entry = self._plugins.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name}")
        return entry.instance

    def list_plugins(self) -> list[PluginMetadata]:
        return [e.metadata for e in self._plugins.values()]

    def has(self, name: str) -> bool:
        return name in self._plugins

    # ── Hook system ──────────────────────────────────────────────────────

    def add_hook(self, event: str, callback: Callable[..., Any]) -> None:
        self._hooks.setdefault(event, []).append(callback)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        for cb in self._hooks.get(event, []):
            results.append(cb(*args, **kwargs))
        return results

    # ── Lifecycle ────────────────────────────────────────────────────────

    def shutdown_all(self) -> None:
        for entry in self._plugins.values():
            if hasattr(entry.instance, "shutdown"):
                entry.instance.shutdown()
        self._plugins.clear()
        self._hooks.clear()


# ── Plugin decorator ─────────────────────────────────────────────────────────

def plugin(
    name: str,
    *,
    version: str = "0.1.0",
    category: str = "general",
    description: str = "",
) -> Callable[[type], type]:
    """Class decorator that attaches plugin metadata."""

    def decorator(cls: type) -> type:
        cls.name = name  # type: ignore[attr-defined]
        cls._plugin_metadata = PluginMetadata(  # type: ignore[attr-defined]
            name=name,
            version=version,
            category=category,
            description=description,
        )
        return cls

    return decorator


# ── Internal ─────────────────────────────────────────────────────────────────

@dataclass
class _PluginEntry:
    cls: type
    instance: Any
    metadata: PluginMetadata
    config: dict[str, Any]
