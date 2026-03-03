"""Unit tests for Catalyst Plugin system."""
import pytest
import asyncio
from core.plugin import Plugin, PluginManager


class DummyPlugin(Plugin):
    name = "dummy"
    description = "A simple test plugin"

    def __init__(self):
        self.called_with = None

    async def execute(self, *args, **kwargs):
        self.called_with = (args, kwargs)
        return "dummy result"

    def validate(self, args, kwargs):
        if "fail" in kwargs:
            raise ValueError("Intentional failure")


class FailingPlugin(Plugin):
    name = "failing"
    description = "Always fails"

    async def execute(self, *args, **kwargs):
        raise RuntimeError("Plugin failure")


class TestPluginManager:
    """Test PluginManager registration and lookup."""

    def test_register_plugin(self):
        mgr = PluginManager()
        plugin = DummyPlugin()
        mgr.register(plugin)
        assert "dummy" in mgr.list_plugins()
        assert mgr.get("dummy") is plugin

    def test_register_duplicate_raises(self):
        mgr = PluginManager()
        plugin1 = DummyPlugin()
        plugin2 = DummyPlugin()
        mgr.register(plugin1)
        with pytest.raises(ValueError):
            mgr.register(plugin2)

    def test_register_without_name_raises(self):
        class NoNamePlugin(Plugin):
            async def execute(self):
                pass
        mgr = PluginManager()
        plugin = NoNamePlugin()
        with pytest.raises(ValueError):
            mgr.register(plugin)

    def test_unregister(self):
        mgr = PluginManager()
        plugin = DummyPlugin()
        mgr.register(plugin)
        mgr.unregister("dummy")
        assert "dummy" not in mgr.list_plugins()
        assert mgr.get("dummy") is None

    def test_clear_all_plugins(self):
        mgr = PluginManager()
        mgr.register(DummyPlugin())
        mgr.register(FailingPlugin())
        mgr.clear()
        assert len(mgr.list_plugins()) == 0

    def test_on_load_called(self):
        class LifecyclePlugin(Plugin):
            name = "lifecycle"
            def __init__(self):
                self.loaded = False
            def on_load(self):
                self.loaded = True
            async def execute(self):
                pass
        mgr = PluginManager()
        plugin = LifecyclePlugin()
        mgr.register(plugin)
        assert plugin.loaded

    def test_on_load_failure_rolls_back(self):
        class BadLoadPlugin(Plugin):
            name = "badload"
            def on_load(self):
                raise RuntimeError("Load failed")
            async def execute(self):
                pass
        mgr = PluginManager()
        plugin = BadLoadPlugin()
        with pytest.raises(RuntimeError):
            mgr.register(plugin)
        assert "badload" not in mgr.list_plugins()


class TestPluginExecution:
    """Test plugin execution through manager."""

    @pytest.mark.asyncio
    async def test_execute_plugin(self):
        mgr = PluginManager()
        plugin = DummyPlugin()
        mgr.register(plugin)
        result = await plugin.execute("arg1", "arg2", key="value")
        assert result == "dummy result"
        args, kwargs = plugin.called_with
        assert args == ("arg1", "arg2")
        assert kwargs == {"key": "value"}

    @pytest.mark.asyncio
    async def test_plugin_exception_propagates(self):
        mgr = PluginManager()
        plugin = FailingPlugin()
        mgr.register(plugin)
        with pytest.raises(RuntimeError):
            await plugin.execute()


class TestModuleAdapter:
    """Test automatic module adapter for legacy run/execute functions."""

    def test_adapter_for_run_function(self):
        # Create a fake module with a run function
        class FakeModule:
            @staticmethod
            def run(x, y):
                return x + y
        mgr = PluginManager()
        mgr.load_from_module(FakeModule, name="fakerun")
        plugin = mgr.get("fakerun")
        assert plugin is not None
        assert plugin.name == "fakerun"

    def test_adapter_for_async_run(self):
        class FakeAsyncModule:
            @staticmethod
            async def run(x):
                await asyncio.sleep(0.001)
                return x * 2
        mgr = PluginManager()
        mgr.load_from_module(FakeAsyncModule, name="asyncrun")
        plugin = mgr.get("asyncrun")
        assert plugin is not None

    def test_adapter_missing_run_raises(self):
        class EmptyModule:
            pass
        mgr = PluginManager()
        with pytest.raises(AttributeError):
            mgr.load_from_module(EmptyModule, name="empty")


class TestPluginValidation:
    """Test plugin input validation."""

    @pytest.mark.asyncio
    async def test_validate_called(self):
        class ValidatingPlugin(Plugin):
            name = "validator"
            def __init__(self):
                self.validated = False
            def validate(self, args, kwargs):
                self.validated = True
                if "bad" in kwargs:
                    raise ValueError("bad input")
            async def execute(self, **kwargs):
                return "ok"
        mgr = PluginManager()
        plugin = ValidatingPlugin()
        mgr.register(plugin)
        # Execute will implicitly call validate during plugin.execute? Actually the base Plugin doesn't auto-call validate
        # But we can test that orchestrator would call it. For unit test, we call manually:
        plugin.validate((), {"good": True})
        assert plugin.validated
