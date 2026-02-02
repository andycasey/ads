"""Configuration settings for the ADS API client using Pydantic."""

import json
import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = ["ADSConfig", "get_config"]


class ADSConfig(BaseModel):
    """Configuration for the ADS API client."""

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    # API Configuration
    api_url: str = Field(
        default="https://api.adsabs.harvard.edu/v1",
        description="Base URL for the ADS API",
    )

    # Token Configuration
    tokens: Optional[List[str]] = Field(
        default=None,
        description="List of API tokens for rotation. If None, will use single token discovery.",
    )

    # Async Request Configuration
    async_limit_per_host: int = Field(
        default=10, ge=1, le=100, description="Maximum concurrent connections per host"
    )

    async_limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum total concurrent connections"
    )

    async_timeout: int = Field(
        default=30, ge=1, description="Timeout for async requests in seconds"
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries for failed requests",
    )

    retry_base_delay: float = Field(
        default=1.0,
        gt=0,
        description="Base delay in seconds for exponential backoff (delay = base * 2^attempt)",
    )

    # Query Configuration
    max_rows_per_request: int = Field(
        default=200,
        ge=1,
        le=200,
        description="Maximum number of rows per API request (ADS limit is 200)",
    )

    # Rate limit threshold for token rotation (conservative threshold)
    rate_limit_threshold: int = Field(
        default=4500,
        ge=0,
        description="Remaining requests threshold to trigger token rotation",
    )

    # Token discovery configuration (legacy support)
    token_files: List[str] = Field(
        default_factory=lambda: [
            "~/.ads/token",
            "~/.ads/dev_key",
        ],
        description="Paths to search for API token files",
    )

    token_environ_vars: List[str] = Field(
        default_factory=lambda: ["ADS_API_TOKEN", "ADS_DEV_KEY"],
        description="Environment variables to check for API tokens",
    )

    @field_validator("tokens", mode="before")
    @classmethod
    def validate_tokens(cls, v):
        """Ensure tokens is a list if provided as a single string."""
        if v is None:
            return None
        if isinstance(v, str):
            # Split by comma if multiple tokens provided as string
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

    @field_validator("token_files", mode="before")
    @classmethod
    def expand_token_files(cls, v):
        """Expand user paths in token files."""
        if isinstance(v, list):
            return [os.path.expanduser(path) for path in v]
        return v

    def discover_tokens(self) -> Optional[List[str]]:
        """
        Discover tokens using legacy token discovery mechanism.
        Returns a list with a single token if found, or None.
        """
        # Check environment variables
        for var in self.token_environ_vars:
            token = os.environ.get(var)
            if token:
                return [token.strip()]

        # Check token files
        for filepath in self.token_files:
            expanded_path = os.path.expanduser(filepath)
            if os.path.exists(expanded_path):
                try:
                    with open(expanded_path, "r") as f:
                        token = f.read().strip()
                        if token:
                            return [token]
                except IOError:
                    continue

        return None

    @classmethod
    def from_file(cls, filepath: str) -> "ADSConfig":
        """
        Load configuration from a JSON or YAML file.

        :param filepath:
            Path to configuration file (.json, .yaml, or .yml)

        :returns:
            ADSConfig instance
        """
        path = Path(filepath).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        with open(path, "r") as f:
            if path.suffix == ".json":
                data = json.load(f)
            elif path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

        return cls(**data)

    @classmethod
    def from_env(cls) -> "ADSConfig":
        """
        Load configuration from environment variables.
        Environment variables should be prefixed with ADS_CONFIG_
        (e.g., ADS_CONFIG_MAX_RETRIES=5)

        :returns:
            ADSConfig instance with values from environment
        """
        env_config = {}
        prefix = "ADS_CONFIG_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                # Handle list values (comma-separated)
                if config_key in ("tokens", "token_files", "token_environ_vars"):
                    env_config[config_key] = [v.strip() for v in value.split(",")]
                # Handle integer values
                elif config_key in (
                    "async_limit_per_host",
                    "async_limit",
                    "async_timeout",
                    "max_retries",
                    "max_rows_per_request",
                    "rate_limit_threshold",
                ):
                    env_config[config_key] = int(value)
                # Handle float values
                elif config_key == "retry_base_delay":
                    env_config[config_key] = float(value)
                else:
                    env_config[config_key] = value

        return cls(**env_config)

    def save(self, path: os.PathLike | Path):
        with open(path, "w") as f:
            import json

            json.dump(ADSConfig().model_dump(), f, indent=4)


# Global configuration instance (singleton-like)
_global_config: Optional[ADSConfig] = None


def get_config(
    config_file: Optional[str] = "~/.ads/config.json", use_env: bool = False, **kwargs
) -> ADSConfig:
    """
    Get or create the global ADSConfig instance.

    Priority order (highest to lowest):
    1. Explicit kwargs passed to this function
    2. Config file (if provided)
    3. Environment variables (if use_env=True)
    4. Default values

    :param config_file: [optional]
        Path to configuration file (.json, .yaml, or .yml)

    :param use_env: [optional]
        Whether to load configuration from environment variables (default: True)

    :param kwargs: [optional]
        Explicit configuration values that override all other sources

    :returns:
        ADSConfig instance
    """
    global _global_config

    # Start with defaults
    config_data = {}

    # Load from environment if requested
    if use_env:
        try:
            env_config = ADSConfig.from_env()
            config_data.update(env_config.model_dump(exclude_unset=True))
        except Exception:
            pass  # Silently ignore env loading errors

    # Load from file if provided
    if config_file:
        file_config = ADSConfig.from_file(config_file)
        config_data.update(file_config.model_dump(exclude_unset=True))

    # Override with explicit kwargs
    config_data.update(kwargs)

    # Create or update global config
    if _global_config is None:
        _global_config = ADSConfig(**config_data)
    else:
        # Update existing config with new values
        for key, value in config_data.items():
            setattr(_global_config, key, value)

    return _global_config


def reset_config():
    """Reset the global configuration to None. Useful for testing."""
    global _global_config
    _global_config = None
