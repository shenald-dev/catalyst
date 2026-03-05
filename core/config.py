"""Configuration management for Catalyst.

Provides layered configuration with precedence:
1. Default values (hardcoded)
2. YAML configuration file (~/.catalyst/config.yaml or $CATALYST_CONFIG)
3. Environment variables (prefix: CATALYST_)
4. Explicit runtime overrides (passed to Orchestrator)

Allows dot-notation access and dictionary-style get.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


@dataclass(frozen=True)
class Config:
    """
    Immutable configuration object for Catalyst.

    Attributes (all optional, defaults shown):
      cpu_limit: float = 0.0 (no limit)
      memory_mb_limit: float = 0.0 (no limit)
      enable_cancellation: bool = True
      enable_tracing: bool = False
      otlp_endpoint: Optional[str] = None
      otlp_headers: Dict[str, str] = field(default_factory=dict)
      otlp_insecure: bool = False
      enable_metrics: bool = False
      metrics_port: Optional[int] = None
      enable_profiling: bool = False
      profile_output: Optional[str] = None
      enable_json_logging: bool = False
      plugin_dirs: list = field(default_factory=lambda: ["plugins/builtin"])
      resource_limits: Dict[str, float] = field(default_factory=dict)
    """
    # Core behavior
    enable_cancellation: bool = True
    enable_tracing: bool = False
    otlp_endpoint: Optional[str] = None
    otlp_headers: Dict[str, str] = field(default_factory=dict)
    otlp_insecure: bool = False

    # Metrics
    enable_metrics: bool = False
    metrics_port: Optional[int] = None

    # Profiling
    enable_profiling: bool = False
    profile_output: Optional[str] = None

    # Logging
    enable_json_logging: bool = False

    # Resources
    cpu_limit: float = 0.0
    memory_mb_limit: float = 0.0
    io_limit: float = 0.0
    resource_limits: Dict[str, float] = field(default_factory=dict)

    # Plugins
    plugin_dirs: list = field(default_factory=lambda: ["plugins/builtin"])

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get with optional default."""
        return getattr(self, key, default)

    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as a plain dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


def _coerce_env_value(key: str, value: str) -> Any:
    """Coerce environment variable string to appropriate type."""
    # Booleans
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False
    # Numbers (int then float)
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            pass
    # JSON-like lists/dicts (comma-separated for simple cases)
    if ',' in value:
        return [item.strip() for item in value.split(',') if item.strip()]
    # Keep as string
    return value


def _expand_nested_env(vars_prefix: str, env: Dict[str, str]) -> Dict[str, Any]:
    """
    Expand environment variables with prefix into a nested config dict.
    Supports simple dot notation for nesting: CATALYST_RESOURCE_CPU_LIMIT -> resource.cpu_limit
    For Phase 5, we map flat keys to Config attributes directly.
    """
    config: Dict[str, Any] = {}
    for raw_key, raw_val in env.items():
        if not raw_key.startswith(vars_prefix):
            continue
        # Remove prefix and lowercase
        key = raw_key[len(vars_prefix):].lower()
        # Map common keys directly
        config[key] = _coerce_env_value(key, raw_val)
    return config


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow merge: override values, don't deep-merge."""
    merged = base.copy()
    merged.update(override)
    return merged


def load_config(
    config_path: Optional[str] = None,
    env_override: bool = True,
    runtime_overrides: Optional[Dict[str, Any]] = None
) -> Config:
    """
    Load Catalyst configuration from all sources with precedence.

    Order (lowest to highest):
      1. Default values from Config dataclass
      2. YAML config file (if exists)
      3. Environment variables (CATALYST_*)
      4. runtime_overrides dict (explicit arguments)

    Args:
      config_path: Explicit path to YAML config file. If None, checks
                   $CATALYST_CONFIG then ~/.catalyst/config.yaml.
      env_override: Whether to apply environment variables.
      runtime_overrides: Dict of config keys to override final values.

    Returns:
      Frozen Config instance.
    """
    # Start with defaults
    defaults = Config().as_dict()

    # Load YAML if exists
    yaml_config: Dict[str, Any] = {}
    if config_path is None:
        # Check env-specified path
        config_path = os.getenv("CATALYST_CONFIG")
        if not config_path:
            # Default to home directory
            home = os.path.expanduser("~")
            config_path = os.path.join(home, ".catalyst", "config.yaml")
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
            # Flatten to one-level dict matching Config attributes
            # For now, expect YAML keys to match Config field names directly
            yaml_config = {k: v for k, v in yaml_data.items() if k in defaults}
        except Exception:
            yaml_config = {}

    # Environment variables
    env_config: Dict[str, Any] = {}
    if env_override:
        env_vars = {k: v for k, v in os.environ.items() if k.startswith("CATALYST_")}
        env_config = _expand_nested_env("CATALYST_", env_vars)
        # Filter keys to known attributes
        env_config = {k: v for k, v in env_config.items() if k in defaults}

    # Runtime overrides
    runtime_config = runtime_overrides or {}

    # Merge in order
    final_config = defaults
    final_config = _merge_dicts(final_config, yaml_config)
    final_config = _merge_dicts(final_config, env_config)
    final_config = _merge_dicts(final_config, runtime_config)

    # Post-process: if resource_limits not set, construct from individual limits
    if not final_config.get('resource_limits'):
        resource_limits: Dict[str, float] = {}
        if final_config.get('cpu_limit', 0) > 0:
            resource_limits['cpu'] = final_config['cpu_limit']
        if final_config.get('memory_mb_limit', 0) > 0:
            resource_limits['memory_mb'] = final_config['memory_mb_limit']
        if final_config.get('io_limit', 0) > 0:
            resource_limits['io'] = final_config['io_limit']
        final_config['resource_limits'] = resource_limits

    return Config(**final_config)
