"""
Plugin system for Catalyst.

Provides:
- Plugin base class with lifecycle hooks
- PluginManager for registration, discovery, and access
- Adapter for legacy modules (with run/execute functions)
"""

import asyncio
import inspect
import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, List
import yaml


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

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        pass

    def health_check(self) -> bool:
        """
        Perform a quick health check to verify the plugin is functional.

        Returns:
            True if healthy, False otherwise.

        Plugins can override this to test external dependencies
        (e.g., database connectivity, API availability).
        """
        return True

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


# --- Plugin Manifest System ---

class PluginManifest:
    """
    Represents a plugin manifest (pyproject.toml style).

    Fields:
      - plugin.name (required)
      - plugin.version
      - plugin.description
      - plugin.dependencies (list of Python packages)
      - config.schema (optional Pydantic model path)
      - config.defaults (dict)
    """
    def __init__(self, name: str, version: str = "0.1.0", description: str = "",
                 dependencies: List[str] = None, config_schema: Optional[str] = None,
                 config_defaults: Dict = None):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.config_schema = config_schema
        self.config_defaults = config_defaults or {}

    @classmethod
    def from_toml(cls, path: str) -> 'PluginManifest':
        """Load a manifest from a YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        plugin_section = data.get('plugin', {})
        config_section = data.get('config', {})
        return cls(
            name=plugin_section['name'],
            version=plugin_section.get('version', '0.1.0'),
            description=plugin_section.get('description', ''),
            dependencies=plugin_section.get('dependencies', []),
            config_schema=config_section.get('schema'),
            config_defaults=config_section.get('defaults', {})
        )

    def validate_dependencies(self) -> List[str]:
        """
        Check if required dependencies are installed.

        Returns:
            List of missing package names.
        """
        missing = []
        for dep in self.dependencies:
            # Simple check: try import
            pkg_name = dep.split('>')[0].split('=')[0].split('<')[0].strip()
            try:
                __import__(pkg_name)
            except ImportError:
                missing.append(dep)
        return missing

    def to_dict(self) -> dict:
        return {
            'plugin': {
                'name': self.name,
                'version': self.version,
                'description': self.description,
                'dependencies': self.dependencies,
            },
            'config': {
                'schema': self.config_schema,
                'defaults': self.config_defaults,
            }
        }


class PluginManager:
    """Manages plugin registration, lookup, and lifecycle."""

    def __init__(self, cache_size: int = 128):
        """
        Initialize plugin manager.

        Args:
            cache_size: Size of LRU cache for plugin lookups (0 to disable).
        """
        self._plugins: Dict[str, Plugin] = {}
        self._cache_size = cache_size
        self._get_cache = {}
        if cache_size > 0:
            # Simple FIFO cache (LRU would be better but keep minimal)
            self._cache_order = []
            self._get_cache = {}

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
        # Invalidate cache entry if present
        if hasattr(self, '_get_cache') and plugin.name in self._get_cache:
            self._get_cache.pop(plugin.name, None)
            if hasattr(self, '_cache_order'):
                try:
                    self._cache_order.remove(plugin.name)
                except ValueError:
                    pass
        try:
            plugin.on_load()
            # Perform a health check after loading
            try:
                healthy = plugin.health_check()
                if not healthy:
                    # Log a warning but continue; plugin is usable but may have issues
                    import warnings
                    warnings.warn(f"Plugin '{plugin.name}' health check reported unhealthy state", RuntimeWarning)
            except Exception as e:
                # Health check itself failed; treat as load failure
                del self._plugins[plugin.name]
                raise RuntimeError(f"Plugin '{plugin.name}' health check failed: {e}") from e
        except Exception:
            # Unregister if on_load fails to keep consistency
            del self._plugins[plugin.name]
            raise

    async def unregister(self, name: str) -> None:
        """
        Unregister a plugin.

        Awaits plugin.on_unload() before removal.
        """
        if name in self._plugins:
            plugin = self._plugins[name]
            await plugin.on_unload()
            del self._plugins[name]
            # Invalidate cache
            if hasattr(self, '_get_cache') and name in self._get_cache:
                self._get_cache.pop(name, None)
                if hasattr(self, '_cache_order'):
                    try:
                        self._cache_order.remove(name)
                    except ValueError:
                        pass

    def get(self, name: str) -> Optional[Plugin]:
        """Retrieve a plugin by name, or None if not found. Uses cache if enabled."""
        if self._cache_size <= 0:
            return self._plugins.get(name)

        # Check cache first
        if name in self._get_cache:
            # Move to end (most recent) if using order tracking
            if self._cache_size > 0 and hasattr(self, '_cache_order'):
                try:
                    self._cache_order.remove(name)
                except ValueError:
                    pass
                self._cache_order.append(name)
            return self._get_cache[name]

        # Cache miss: fetch from source
        plugin = self._plugins.get(name)
        if plugin is not None:
            # Insert into cache
            if len(self._cache_order) >= self._cache_size:
                # Evict oldest
                oldest = self._cache_order.pop(0)
                self._get_cache.pop(oldest, None)
            self._cache_order.append(name)
            self._get_cache[name] = plugin
        return plugin

    def list_plugins(self) -> list:
        """Return list of registered plugin names."""
        return list(self._plugins.keys())

    async def clear(self) -> None:
        """Unregister all plugins."""
        for name in list(self._plugins.keys()):
            await self.unregister(name)
        # Clear cache fully
        if hasattr(self, '_get_cache'):
            self._get_cache.clear()
        if hasattr(self, '_cache_order'):
            self._cache_order.clear()

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
                doc = getattr(mod, "__doc__", None) or ""
                self.description = doc.strip() or "Module adapter"

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

            async def on_unload(self):
                pass

        adapter = ModuleAdapter(module, name or module.__name__.split('.')[-1])
        self.register(adapter)
        return adapter

    def _load_schema_class(self, schema_path: str):
        """
        Import and return a class from a module path string.

        Args:
            schema_path: Like "plugins.builtin.database_config:DatabaseConfig" or "module.submodule:Model".

        Returns:
            The imported class.
        """
        if ':' in schema_path:
            module_name, attr_name = schema_path.split(':', 1)
        elif '.' in schema_path and ' ' not in schema_path:
            # Heuristic: last dot separates module and class
            parts = schema_path.rsplit('.', 1)
            if len(parts) == 2:
                module_name, attr_name = parts
            else:
                module_name = schema_path
                attr_name = None
        else:
            module_name = schema_path
            attr_name = None
        module = importlib.import_module(module_name)
        if attr_name:
            cls = getattr(module, attr_name)
        else:
            # Assume the module itself is the class (unlikely)
            cls = module
        return cls

    def load_manifest(self, manifest_path: str, plugin_cls: Type[Plugin], auto_install: bool = False) -> Plugin:
        """
        Load a plugin from a manifest and a Plugin subclass.

        Args:
            manifest_path: Path to the plugin's manifest TOML file.
            plugin_cls: The Plugin subclass to instantiate.
            auto_install: If True, attempt to install missing dependencies via pip.

        Returns:
            The registered plugin instance.

        The manifest provides metadata and config defaults. The plugin_cls
        should accept config values via __init__ or a configure() method.
        """
        manifest = PluginManifest.from_toml(manifest_path)

        # Check dependencies
        missing = manifest.validate_dependencies()
        if missing:
            if auto_install:
                # Attempt to install missing dependencies automatically
                installed = self._auto_install_dependencies(missing)
                # Re-validate after installation attempt
                still_missing = manifest.validate_dependencies()
                if still_missing:
                    raise RuntimeError(
                        f"Failed to install dependencies for plugin '{manifest.name}': {', '.join(still_missing)}"
                    )
            else:
                import warnings
                warnings.warn(
                    f"Plugin '{manifest.name}' missing dependencies: {', '.join(missing)}",
                    RuntimeWarning
                )

        # Instantiate plugin, passing config defaults
        try:
            # Try to pass config via constructor if it accepts **kwargs
            plugin = plugin_cls(**manifest.config_defaults)
        except TypeError:
            # Maybe plugin has a configure method
            plugin = plugin_cls()
            if hasattr(plugin, 'configure'):
                plugin.configure(**manifest.config_defaults)
            # Otherwise ignore defaults
        # Override name from manifest
        plugin.name = manifest.name
        plugin.version = manifest.version
        if not plugin.description:
            plugin.description = manifest.description

        # Perform config validation if schema provided
        if manifest.config_schema:
            try:
                # Import Pydantic if available
                import pydantic
                from pydantic import ValidationError
            except ImportError as e:
                raise ImportError(
                    f"Plugin '{manifest.name}' specifies a config_schema but Pydantic is not installed. "
                    "Install pydantic to enable schema validation."
                ) from e
            try:
                schema_cls = self._load_schema_class(manifest.config_schema)
            except Exception as e:
                raise ImportError(
                    f"Failed to import config schema '{manifest.config_schema}' for plugin '{manifest.name}': {e}"
                ) from e
            # Merge defaults with any runtime config already set on plugin (if any)
            # For simplicity, validate against defaults; later runtime config override should also be validated via Plugin.validate
            try:
                # If plugin already has a config dict attribute, merge
                runtime_config = getattr(plugin, 'config', {})
                combined_config = {**manifest.config_defaults, **runtime_config}
                validated = schema_cls(**combined_config)
                # Store validated config back on plugin
                plugin.config = validated
                # Also set attributes for convenience
                plugin.config_dict = validated.dict()
            except ValidationError as ve:
                raise ValueError(
                    f"Configuration validation failed for plugin '{manifest.name}': {ve}"
                ) from ve

        self.register(plugin)
        return plugin

    def _auto_install_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Attempt to install a list of Python packages using pip.

        Args:
            dependencies: List of package specifiers (e.g., ["aiohttp>=3.0", "pydantic"]).

        Returns:
            List of packages that were successfully installed.

        Raises:
            subprocess.CalledProcessError if pip installation fails for any package.
        """
        import subprocess
        import sys
        installed = []
        for dep in dependencies:
            # Check if already available (maybe installed in the meantime)
            pkg_name = dep.split('>')[0].split('=')[0].split('<')[0].strip()
            try:
                __import__(pkg_name)
                continue  # already available
            except ImportError:
                pass
            # Install using pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, [sys.executable, "-m", "pip", "install", dep], result.stderr
                )
            installed.append(dep)
        return installed
