from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
DEFAULT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


@dataclass
class LLMSettings:
    url: str
    api_key: str
    model_tree: Dict[str, Dict[str, List[str]]]
    default_model: Optional[str] = None  # When set, use this model name directly (no tree)


class ConfigError(Exception):
    pass


def _normalize_url(value: str) -> str:
    return value.strip().rstrip("/")


def _load_api_key_for_url(url: str) -> str:
    # Support local runs and docker-compose volume mount (/app/.env).
    load_dotenv(DEFAULT_ENV_PATH, override=False)

    normalized_url = _normalize_url(url)

    keys_json = os.getenv("LLM_API_KEYS", "").strip()
    if keys_json:
        try:
            key_map = json.loads(keys_json)
        except json.JSONDecodeError as e:
            raise ConfigError("Invalid LLM_API_KEYS in .env: must be valid JSON object.") from e
        if not isinstance(key_map, dict):
            raise ConfigError("Invalid LLM_API_KEYS in .env: must be a JSON object.")

        normalized_map: Dict[str, str] = {}
        for k, v in key_map.items():
            if isinstance(k, str) and isinstance(v, str) and v.strip():
                normalized_map[_normalize_url(k)] = v.strip()

        matched_key = normalized_map.get(normalized_url)
        if matched_key:
            return matched_key

    # Optional fallback: host-based env var name, e.g. LLM_API_KEY_O3_FAN
    host = urlparse(normalized_url).hostname or ""
    if host:
        host_var = "LLM_API_KEY_" + "".join(ch if ch.isalnum() else "_" for ch in host.upper())
        host_key = os.getenv(host_var, "").strip()
        if host_key:
            return host_key

    # Backward-compatible single key fallback.
    single_key = os.getenv("LLM_API_KEY", "").strip()
    if single_key:
        return single_key

    raise ConfigError(
        "No API key found for llm.url. Set LLM_API_KEYS JSON in backend/.env "
        "(recommended) or fallback LLM_API_KEY."
    )


def load_yaml_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ConfigError("YAML config must be a dictionary.")

    return data


def load_llm_settings(config_path: str | Path = DEFAULT_CONFIG_PATH) -> LLMSettings:
    data = load_yaml_config(config_path)

    llm = data.get("llm")
    if not isinstance(llm, dict):
        raise ConfigError("Missing or invalid 'llm' section in config.")

    url = llm.get("url")
    model_val = llm.get("model")

    if not isinstance(url, str) or not url.strip():
        raise ConfigError("Invalid llm.url in config.")
    api_key = _load_api_key_for_url(url)

    if isinstance(model_val, str) and model_val.strip():
        model_tree = {}
        default_model = model_val.strip()
    elif isinstance(model_val, dict) and model_val:
        model_tree = model_val
        default_model = None
    else:
        raise ConfigError("Invalid llm.model in config: must be a non-empty string or a model tree dict.")

    return LLMSettings(
        url=url.strip(),
        api_key=api_key,
        model_tree=model_tree,
        default_model=default_model,
    )


def resolve_model_endpoint(
    model_tree: Dict[str, Dict[str, List[str]]],
    provider: Optional[str] = None,
    series: Optional[str] = None,
    index: int = 0,
    endpoint_id: Optional[str] = None,
    default_model: Optional[str] = None,
) -> str:
    """
    解析最终传给 OpenAI-compatible SDK 的 model 值。
    当 default_model 存在且未指定 endpoint_id 时，直接返回 default_model；
    否则从 model_tree 按 provider/series/index 解析，或返回 endpoint_id。
    """
    if endpoint_id:
        return endpoint_id
    if default_model:
        return default_model

    if not provider:
        raise ConfigError("provider is required when endpoint_id and default_model are not set.")
    if not series:
        raise ConfigError("series is required when endpoint_id and default_model are not set.")

    provider_block = model_tree.get(provider)
    if not isinstance(provider_block, dict):
        raise ConfigError(f"Provider '{provider}' not found in config.")

    series_block = provider_block.get(series)
    if not isinstance(series_block, list) or not series_block:
        raise ConfigError(f"Series '{series}' not found under provider '{provider}'.")

    if index < 0 or index >= len(series_block):
        raise ConfigError(
            f"Model index out of range for provider='{provider}', series='{series}', index={index}."
        )

    endpoint = series_block[index]
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ConfigError("Resolved endpoint id is invalid.")

    return endpoint.strip()
