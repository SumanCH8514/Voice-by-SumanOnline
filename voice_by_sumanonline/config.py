from __future__ import annotations

import copy
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

log = logging.getLogger("voice_by_sumanonline.config")

CONFIG_DIR = Path.home() / ".config" / "voice_by_sumanonline"
CONFIG_PATH = CONFIG_DIR / "config.json"

def default_config() -> Dict[str, Any]:
    return {
        "hotkey": "Key.alt_r",
        "toggle_mode": False,
        "pre_roll_ms": 0,
        "input_device": None,
        "overlay_enabled": True,
        "start_on_login": False,
        "style_preset": "smart",
        "custom_prompt": "",
        "transcription": {
            "model": "base",
            "preview_enabled": True,
        },
        "format": {
            "tier": "auto",
            "groq_model": "qwen/qwen3.8-27b",
            "ollama_model": "llama3.2:3b",
        },
        "dictionary": [
            ["suman online", "SumanOnline"],
            ["kubernetes", "K8s"],
            ["pie torch", "PyTorch"],
            ["next js", "Next.js"],
            ["grpc", "gRPC"],
            ["whisper flow", "Wispr Flow"],
        ],
        "stats": {
            "total_dictations": 0,
            "total_words": 0,
            "total_seconds_recorded": 0.0,
        },
        "server": {
            "port": 48922,
            "host": "127.0.0.1",
        },
    }

def load_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    cfg = default_config()
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                on_disk = json.load(f)
            _deep_merge(cfg, on_disk)
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Config at %s unreadable (%s); using defaults.", path, e)
    return cfg

def save_config(cfg: Dict[str, Any], path: Path = CONFIG_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_cfg = copy.deepcopy(cfg)
    clean_cfg.pop("api_key", None)
    clean_cfg.pop("groq_api_key", None)
    if "format" in clean_cfg and isinstance(clean_cfg["format"], dict):
        clean_cfg["format"].pop("api_key", None)
        clean_cfg["format"].pop("groq_api_key", None)
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(clean_cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except OSError as e:
        log.error("Failed to write config: %s", e)
        raise

def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> None:
    for k, v in overlay.items():
        if (
            k in base
            and isinstance(base[k], dict)
            and isinstance(v, dict)
        ):
            _deep_merge(base[k], v)
        else:
            base[k] = v

def get_dictionary(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    raw = cfg.get("dictionary") or []
    out: List[Tuple[str, str]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            f, r = item
            if f:
                out.append((str(f).strip(), str(r).strip()))
    return out
