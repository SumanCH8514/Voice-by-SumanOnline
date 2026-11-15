# Voice by SumanOnline

A fast, cross-platform push-to-talk and hands-free AI voice dictation desktop application built with the exact experience of **Wispr Flow**.

Hold **Right Alt / Right Option** (or tap to toggle in hands-free mode) to speak, and release to automatically transcribe locally with Faster-Whisper, clean up with anti-hallucination AI formatting, and paste the text directly at your active cursor across any application without stealing window focus.

---

## Highlights & Features

### 1. Modern Desktop Experience (Wispr Flow Style)
- **Floating HUD Pill**: A non-activating, glassmorphic HUD overlay floating gracefully above your taskbar. Includes real-time audio-reactive soundwave visualizer, live provisional transcript preview, and state indicators.
- **Voice Studio Dashboard**: Full desktop studio with interactive dictation playground, raw vs polished comparison, live latency telemetry, and input dB meters.
- **Hands-Free Toggle Mode**: Choose between classic push-to-talk (hold to speak) or toggle mode (tap once to begin, tap again to finish and inject).

### 2. Intelligent Prompt & Style Presets
- **Smart Dictation (Wispr Flow Flagship)**: Resolves speech repairs and self-corrections ("tomorrow at 2 wait actually 4" → "tomorrow at 4:00"), strips filler words ("um", "uh", "you know", "basically"), maps spoken punctuation, and never follows spoken questions/commands as instructions.
- **Executive & Formal**: Polished corporate communication for emails, memos, and executive updates.
- **Casual & Direct**: Natural, friendly conversational tone for Slack, WhatsApp, and social messaging.
- **Structured Notes**: Automatically converts stream-of-consciousness speech into structured markdown bullet points.
- **Developer / Code Mode**: Preserves camelCase, snake_case, PascalCase, terminal flags, and wraps code tokens in markdown backticks.
- **Custom Prompt Studio**: Define and test your own system instructions interactively with the prompt sandbox.

### 3. Personal Replacement Dictionary
- Word-boundary and case-insensitive replacements applied immediately after transcript cleanup (e.g., `"suman online" → "SumanOnline"`, `"pie torch" → "PyTorch"`, `"kubernetes" → "K8s"`).
- Add, search, delete, and import/export dictionary rules via JSON.

### 4. Productivity Analytics
- Live dashboard displaying total dictations, total words spoken, and estimated typing hours saved (calculated based on average 150 wpm speech vs 40 wpm typing).
- Searchable transcript history log with one-click copy and processing latency metrics.

### 5. Multi-Tier AI Cleanup Pipeline
- **Tier 1 — Groq Cloud**: Sub-200ms latency formatting via fast LLMs (`qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`). Key is stored securely in the native OS Keychain via `keyring` (never stored in plaintext).
- **Tier 2 — Local Ollama**: Zero-cloud private local LLM fallback (`llama3.2:3b` at `http://localhost:11434`).
- **Tier 3 — Deterministic Offline Rule Engine**: Pure-regex offline fallback that strips filler words, maps spoken punctuation, and formats sentence casing.

### 6. Hardware Audio Resilience
- Opens microphones at their native sample rate and downmixes to 16 kHz mono via polyphase resampling (`scipy.signal.resample_poly`).
- Detects continuous digital silence or PortAudio wireless disconnects, reinitializes the audio backend, and switches to fallback microphones automatically.

---

## Project Structure

```
├── voice_by_sumanonline/      # Core Voice Engine & Desktop Backend
│   ├── audio.py               # Resilient audio capture & polyphase resampling
│   ├── config.py              # Configuration manager (~/.config/voice_by_sumanonline)
│   ├── dictionary.py          # Word-boundary personal dictionary engine
│   ├── format.py              # 3-tier cleanup with 5 Wispr Flow style presets
│   ├── history.py             # Dictation history log and analytics tracking
│   ├── hotkey.py              # Push-to-talk & hands-free toggle listener
│   ├── hud.py                 # Non-activating floating HUD overlay
│   ├── inject.py              # Cursor text injection & clipboard restore
│   ├── keychain.py            # OS Keychain integration for API keys
│   ├── preview.py             # Streaming live preview via Vosk
│   ├── server.py              # FastAPI & WebSocket bridge (port 48922)
│   ├── startup.py             # Windows Run registry & startup integration
│   ├── transcribe.py          # Local speech recognition via faster-whisper
│   ├── tray.py                # System tray icon & background controller
│   └── main.py                # Main orchestration loop
├── crates/voice-launcher/     # Native Windows Rust desktop launcher (silent, single-instance)
│   ├── Cargo.toml
│   └── src/main.rs
├── ui/                        # Modern React 19 + TypeScript + Tailwind UI
│   ├── src/
│   │   ├── components/        # Studio, Presets, Dictionary, History, Audio, HUD
│   │   ├── services/          # REST & WebSocket API client
│   │   └── App.tsx            # Desktop studio interface
│   ├── package.json
│   └── vite.config.ts
├── installer/                 # Installation scripts
│   ├── install.ps1            # Automated PowerShell desktop & shortcut installer
│   └── setup.bat              # One-click Windows setup runner
├── start_desktop.bat          # Instant double-click launcher
└── pyproject.toml             # Project manifest & dependencies
```

---

## Installation & Setup

### Windows 10 / 11

#### 1. Windows Installer (.msi Package)
Double-click the generated MSI package:
- **`installer\dist\Voice-by-SumanOnline-Setup.msi`**

Or rebuild/regenerate anytime via:
```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build_msi.ps1
```

#### 2. One-Click Setup Script
Double-click `installer\setup.bat` or run in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\installer\install.ps1
```
This automatically:
- Synchronizes the Python environment with `uv`
- Creates a Start Menu shortcut: `Voice by SumanOnline`
- Creates a Desktop shortcut: `Voice by SumanOnline.lnk`

#### 3. Running the Application
Double-click `start_desktop.bat` or launch from terminal:
```powershell
uv run python -m voice_by_sumanonline.main --ui
```

### Keyboard Shortcuts
- **Hold Right Alt**: Speak while held, release to paste.
- **Hands-Free Mode**: Toggle on in Settings to tap once to speak, tap again to paste.
- On European/international keyboards, **AltGr** is recognized automatically.

---

## License
MIT License.
