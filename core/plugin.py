"""
Plugin system for Catalyst.

Provides:
- Plugin base class with lifecycle hooks
- PluginManager for registration, discovery, and access
- Adapter for legacy modules (with run/execute functions)
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Plugin(ABC):
    """
    Base class for Catalyst plugins.

    Plugins must define a name and an execute method.
    They can optionally implement on_load, on_unload, and validate.
    """
    name: str = None
    version: str = "0.1.0"
    description: str = ""

    def on_load(self) -> None:
        """Called when the plugin is loaded by the manager."""
        pass

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        pass

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Perform the plugin's primary functionality."""
        pass

    def validate(self, args: tuple, kwargs: dict) -> None:
        """
        Optional input validation.

        Raise ValueError if arguments are invalid.
        """
        pass


class PluginManager:
    """Manages plugin registration, lookup, and lifecycle."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin instance.

        Args:
            plugin: Plugin instance with a unique name.

        Raises:
            ValueError: If name is missing or already registered.
        """
        if not plugin.name:
            raise ValueError("Plugin must have a 'name' attribute")
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin
        try:
            plugin.on_load()
        except Exception as e:
            # Unregister if on_load fails to keep consistency
            del self._plugins[plugin.name]
            raise

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin.

        Calls plugin.on_unload() before removal.
        """
        if name in self._plugins:
            self._plugins[name].on_unload()
            del self._plugins[name]

    def get(self, name: str) -> Optional[Plugin]:
        """Retrieve a plugin by name, or None if not found."""
        return self._plugins.get(name)

    def list_plugins(self) -> list:
        """Return list of registered plugin names."""
        return list(self._plugins.keys())

    def clear(self) -> None:
        """Unregister all plugins."""
        for name in list(self._plugins.keys()):
            self.unregister(name)

    def load_from_module(self, module, plugin_class=None, name: str = None):
        """
        Load a plugin from a Python module.

        Supports two modes:
        - If plugin_class is provided: instantiate it and register.
        - If module provides 'run' or 'execute' functions: create a generic adapter.

        Args:
            module: Imported Python module.
            plugin_class: Optional Plugin subclass to instantiate.
            name: Optional explicit plugin name (defaults to module __name__).
        """
        if plugin_class:
            plugin = plugin_class()
            if name:
                plugin.name = name
            self.register(plugin)
            return plugin

        # Auto-discover a Plugin subclass in the module
        plugin_cls = None
        for _, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                plugin_cls = obj
                break
        if plugin_cls:
            plugin = plugin_cls()
            if name:
                plugin.name = name
            self.register(plugin)
            return plugin

        # Auto-adapter for modules with run/execute
        class ModuleAdapter(Plugin):
            def __init__(self, mod, default_name):
                self._mod = mod
                self.name = name or default_name
                self.version = getattr(mod, "__version__", "0.0.1")
                self.description = getattr(mod, "__doc__", "").strip() or "Module adapter"

            async def execute(self, *args, **kwargs):
                if hasattr(self._mod, "run"):
                    fn = self._mod.run
                elif hasattr(self._mod, "execute"):
                    fn = self._mod.execute
                else:
                    raise AttributeError(f"Module '{self._mod.__name__}' has no run/execute")
                if asyncio.iscoroutinefunction(fn):
                    return await fn(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

            def on_load(self):
                pass

            def on_unload(self):
                pass

        adapter = ModuleAdapter(module, name or module.__name__.split('.')[-1])
        self.register(adapter)
        return adapter
