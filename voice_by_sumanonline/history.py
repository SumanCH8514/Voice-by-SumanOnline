from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("voice_by_sumanonline.history")

HISTORY_FILE = Path.home() / ".config" / "voice_by_sumanonline" / "history.json"
MAX_HISTORY_ENTRIES = 500

@dataclass
class HistoryEntry:
    id: str
    timestamp: str
    raw_text: str
    cleaned_text: str
    preset: str
    tier: str
    audio_duration_s: float
    latency_s: float
    word_count: int
    whisper_s: float = 0.0
    format_s: float = 0.0

def load_history() -> List[Dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        log.warning("Could not read history: %s", e)
    return []

def save_history(entries: List[Dict[str, Any]]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(entries[:MAX_HISTORY_ENTRIES], f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, HISTORY_FILE)
    except Exception as e:
        log.warning("Could not save history: %s", e)

def record_dictation(
    raw_text: str,
    cleaned_text: str,
    preset: str,
    tier: str,
    audio_duration_s: float,
    latency_s: float,
    whisper_s: float = 0.0,
    format_s: float = 0.0,
) -> HistoryEntry:
    entry = HistoryEntry(
        id=f"rec_{int(time.time() * 1000)}",
        timestamp=datetime.now().isoformat(),
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        preset=preset,
        tier=tier,
        audio_duration_s=round(audio_duration_s, 2),
        latency_s=round(latency_s, 2),
        word_count=len(cleaned_text.split()),
        whisper_s=round(whisper_s, 2),
        format_s=round(format_s, 2),
    )
    entries = load_history()
    entries.insert(0, asdict(entry))
    save_history(entries)
    return entry

def clear_all_history() -> None:
    save_history([])

def get_stats_summary() -> Dict[str, Any]:
    entries = load_history()
    total_dictations = len(entries)
    total_words = sum(e.get("word_count", 0) for e in entries)
    total_audio_s = sum(e.get("audio_duration_s", 0.0) for e in entries)
    saved_minutes = round((total_words / 40.0) - (total_words / 150.0), 1) if total_words > 0 else 0.0
    return {
        "total_dictations": total_dictations,
        "total_words": total_words,
        "total_audio_seconds": round(total_audio_s, 1),
        "estimated_minutes_saved": max(0.0, saved_minutes),
        "recent_count": min(total_dictations, 50),
    }
