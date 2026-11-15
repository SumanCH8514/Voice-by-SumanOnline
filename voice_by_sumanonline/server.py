from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import get_dictionary, load_config, save_config
from .dictionary import compile_dictionary
from .format import clean_transcript
from .history import clear_all_history, get_stats_summary, load_history
from .keychain import get_api_key, set_api_key, test_connection

log = logging.getLogger("voice_by_sumanonline.server")

app = FastAPI(title="Voice by SumanOnline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: Dict[str, Any]) -> None:
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                self.active_connections.remove(d)

    def threadsafe_broadcast(self, data: Dict[str, Any]) -> None:
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast_json(data), self._loop)

ws_manager = ConnectionManager()

class ConfigUpdate(BaseModel):
    hotkey: Optional[str] = None
    toggle_mode: Optional[bool] = None
    input_device: Optional[Any] = None
    overlay_enabled: Optional[bool] = None
    start_on_login: Optional[bool] = None
    style_preset: Optional[str] = None
    custom_prompt: Optional[str] = None
    transcription: Optional[Dict[str, Any]] = None
    format: Optional[Dict[str, Any]] = None

class KeyUpdate(BaseModel):
    api_key: str

class TestPromptRequest(BaseModel):
    text: str
    style_preset: Optional[str] = "smart"
    custom_prompt: Optional[str] = None
    tier_override: Optional[str] = None

_engine_state_callback: Optional[Any] = None

def set_engine_state_callback(cb: Any) -> None:
    global _engine_state_callback
    _engine_state_callback = cb

@app.on_event("startup")
async def startup_event() -> None:
    loop = asyncio.get_running_loop()
    ws_manager.set_loop(loop)

@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    cfg = load_config()
    engine_status = _engine_state_callback() if _engine_state_callback else {}
    has_groq_key = bool(get_api_key())
    return {
        "status": "ready",
        "app_name": "Voice by SumanOnline",
        "has_key": has_groq_key,
        "style_preset": cfg.get("style_preset", "smart"),
        "toggle_mode": cfg.get("toggle_mode", False),
        "hotkey": cfg.get("hotkey", "Key.alt_r"),
        "whisper_model": cfg.get("transcription", {}).get("model", "base"),
        "preview_enabled": cfg.get("transcription", {}).get("preview_enabled", True),
        **engine_status,
    }

@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    cfg = load_config()
    clean = dict(cfg)
    clean["has_key"] = bool(get_api_key())
    return clean

@app.post("/api/config")
async def update_config(update: ConfigUpdate) -> Dict[str, Any]:
    cfg = load_config()
    data = update.dict(exclude_unset=True)
    for k, v in data.items():
        if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    save_config(cfg)
    from .main import get_global_app_state, apply_live_config
    app_state = get_global_app_state()
    if app_state:
        apply_live_config(cfg)
    ws_manager.threadsafe_broadcast({"type": "config_updated", "config": cfg})
    return {"success": True, "config": cfg}

@app.get("/api/devices")
async def list_devices() -> Dict[str, Any]:
    import sounddevice as sd
    devices_list = []
    default_input_idx = None
    try:
        devs = sd.query_devices()
        try:
            default_dev = sd.query_devices(kind="input")
            default_input_idx = default_dev.get("index")
        except Exception:
            pass
        for i, d in enumerate(devs):
            if d.get("max_input_channels", 0) > 0:
                devices_list.append({
                    "index": i,
                    "name": d.get("name", "Unknown"),
                    "channels": int(d.get("max_input_channels", 1)),
                    "sample_rate": int(d.get("default_samplerate", 16000)),
                    "is_default": (i == default_input_idx),
                })
    except Exception as e:
        log.warning("Could not query devices: %s", e)
    return {"devices": devices_list, "default_index": default_input_idx}

@app.get("/api/history")
async def get_history_items() -> Dict[str, Any]:
    history = load_history()
    stats = get_stats_summary()
    return {"history": history, "stats": stats}

@app.delete("/api/history")
async def delete_history() -> Dict[str, Any]:
    clear_all_history()
    return {"success": True}

@app.get("/api/dictionary")
async def get_dictionary_items() -> Dict[str, Any]:
    cfg = load_config()
    return {"dictionary": cfg.get("dictionary", [])}

@app.post("/api/dictionary")
async def save_dictionary_items(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = payload.get("dictionary", [])
    cfg = load_config()
    cfg["dictionary"] = items
    save_config(cfg)
    from .main import get_global_app_state, apply_live_config
    apply_live_config(cfg)
    return {"success": True, "dictionary": items}

@app.get("/api/key")
async def check_key() -> Dict[str, Any]:
    key = get_api_key()
    return {"has_key": bool(key)}

@app.post("/api/key")
async def update_key(payload: KeyUpdate) -> Dict[str, Any]:
    val = payload.api_key.strip() if payload.api_key else None
    ok = set_api_key(val)
    if not ok:
        return JSONResponse(status_code=500, content={"success": False, "message": "Failed to update keyring."})
    return {"success": True, "has_key": bool(val)}

@app.post("/api/test-key")
async def test_key_connection(payload: KeyUpdate) -> Dict[str, Any]:
    ok, msg = test_connection(payload.api_key)
    return {"success": ok, "message": msg}

@app.post("/api/dictate/test")
async def test_dictate(req: TestPromptRequest) -> Dict[str, Any]:
    cfg = load_config()
    fmt_cfg = cfg.get("format", {})
    key = get_api_key()
    res = clean_transcript(
        req.text,
        groq_api_key=key,
        groq_model=fmt_cfg.get("groq_model", "qwen/qwen3.8-27b"),
        ollama_model=fmt_cfg.get("ollama_model", "llama3.2:3b"),
        tier_override=req.tier_override or fmt_cfg.get("tier", "auto"),
        dictionary=get_dictionary(cfg),
        style_preset=req.style_preset or cfg.get("style_preset", "smart"),
        custom_prompt=req.custom_prompt or cfg.get("custom_prompt", ""),
    )
    return {
        "raw": req.text,
        "cleaned": res.text,
        "tier": res.tier,
        "latency_s": round(res.latency_s, 3),
        "word_count_in": res.word_count_in,
        "word_count_out": res.word_count_out,
    }

@app.post("/api/toggle-recording")
async def toggle_recording_manual() -> Dict[str, Any]:
    from .main import get_global_app_state, manual_trigger_dictation
    state = manual_trigger_dictation()
    return {"success": True, "state": state}

@app.post("/api/toggle-mute")
async def toggle_mute() -> Dict[str, Any]:
    from .main import get_global_app_state, toggle_global_mute
    muted = toggle_global_mute()
    return {"success": True, "muted": muted}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

ui_dist = Path(__file__).resolve().parent.parent / "ui" / "dist"
if ui_dist.exists() and (ui_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="static_ui")
