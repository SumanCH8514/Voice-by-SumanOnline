# Voice by SumanOnline

<div align="center">

![Voice by SumanOnline Logo](assets/Voice%20by%20SumanOnline%20logo.png)

### Intelligent AI Voice Dictation Desktop Application for Windows
**A SumanOnline Project**

[![Release](https://img.shields.io/github/v/release/SumanCH8514/Voice-by-SumanOnline?color=6366F1&label=Release&style=flat-square)](https://github.com/SumanCH8514/Voice-by-SumanOnline/releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20(x64)-0078D4?style=flat-square&logo=windows)](https://github.com/SumanCH8514/Voice-by-SumanOnline/releases/latest)
[![Engine](https://img.shields.io/badge/ASR-Faster--Whisper%20(Local%20Offline)-10B981?style=flat-square)](https://github.com/SYSTRAN/faster-whisper)
[![Runtime](https://img.shields.io/badge/Python-3.12%20Standalone%20Bundled-F59E0B?style=flat-square&logo=python)](https://github.com/SumanCH8514/Voice-by-SumanOnline)
[![License](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat-square)](LICENSE)

[Download Setup (.exe)](https://github.com/SumanCH8514/Voice-by-SumanOnline/releases/latest) • [Official Website](https://sumanch8514.github.io/Voice-by-SumanOnline/) • [Report Issue](https://github.com/SumanCH8514/Voice-by-SumanOnline/issues)

</div>

---

## Overview

**Voice by SumanOnline** is a high-performance, system-wide AI voice dictation desktop application engineered with the precision and responsiveness of **Wispr Flow**.

Press and hold **Right Alt** (or **double-tap for hands-free mode**) to speak from anywhere in Windows. Release the key, and Voice by SumanOnline automatically transcribes your speech locally using Faster-Whisper, cleans up filler words and speech repairs through a multi-tier AI formatting pipeline, and injects the formatted text directly at your active cursor across any desktop application without stealing focus.

---

## Core Capabilities

### 1. Modern Desktop Integration
- **Non-Activating Floating HUD**: A glassmorphic HUD pill overlay positioned above your taskbar. It remains click-transparent and never steals keyboard focus from Word, Slack, VS Code, Discord, or your browser.
- **Dual Hotkey Modes**:
  - **Push-to-Talk**: Hold **Right Alt** (or AltGr) to dictate; release to transcribe and auto-inject.
  - **Hands-Free Double-Tap**: Rapidly double-tap Right Alt to latch recording on. Speak freely, then tap once more to finalize and paste.
- **Native Windows Shell**: Built with Microsoft Edge WebView2 via `pywebview`, delivering a responsive desktop UI running on local loopback IPC.

### 2. Five Wispr Flow Style Presets
- **Smart Dictation**: Strips verbal disfluencies ("um", "uh", "like"), resolves self-corrections (e.g., *"meet me at four wait sorry five"* becomes *"meet me at 5:00"*), and converts spoken punctuation into typographic marks.
- **Executive & Formal**: Structures thoughts into corporate memos, formal business emails, and executive reports.
- **Casual & Direct**: Conversational tone tailored for fast team chats on Slack, Teams, WhatsApp, and Discord.
- **Bullet Notes**: Transforms stream-of-consciousness brainstorms into structured markdown outlines and action items.
- **Developer / Code Mode**: Preserves identifiers, camelCase, snake_case, terminal flags, and backtick code spans.

### 3. Personal Replacement Dictionary
- Custom word-boundary and regex replacement rules executed immediately post-cleanup.
- Ensures domain-specific acronyms, technical libraries, and proper nouns are capitalized and formatted exactly as intended (e.g., `suman online` → `SumanOnline`, `pie torch` → `PyTorch`).

### 4. 3-Tier Resilient AI Pipeline
- **Tier 1 — Groq Cloud**: Sub-200ms latency formatting via high-throughput LLMs (`qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`). Keys are encrypted in the Windows Credential Manager via OS Keychain APIs.
- **Tier 2 — Local Ollama**: Zero-cloud private fallback executing `llama3.2:3b` at `http://127.0.0.1:11434`.
- **Tier 3 — Deterministic Offline Rule Engine**: Pure-regex offline fallback guaranteeing punctuation restoration and verbal filler elimination even with zero internet connectivity.

### 5. Acoustic Resilience
- Polyphase anti-aliasing resampling (`scipy.signal.resample_poly`) converts hardware-native microphone rates (44.1 kHz, 48 kHz, 96 kHz) into pristine 16 kHz mono frames.
- Detects hardware silence and PortAudio device dropouts with automatic fallback to secondary input devices.

---

## Architecture

```
[ Microphone Capture ]
         │ (Native Sample Rate)
         ▼
[ Polyphase Resampler ] ──> 16 kHz Mono Float32
         │
         ├──> [ Vosk Engine ] ──> Streaming Interim Preview HUD
         │
         ▼ (Key Release / Unlatch)
[ Faster-Whisper ASR ] ──> Raw Whisper Transcription
         │
         ▼
[ 3-Tier AI Formatter ] (Smart / Executive / Casual / Notes / Developer)
   ├── Tier 1: Groq Cloud API (<200ms)
   ├── Tier 2: Local Ollama (127.0.0.1:11434)
   └── Tier 3: Deterministic Regex Engine (Offline)
         │
         ▼
[ Personal Dictionary ] ──> Domain-specific terminology replacement
         │
         ▼
[ Win32 Cursor Injector ] ──> Synthesizes Ctrl+V at active window without focus loss
```

---

## Installation

### For Users (Standalone Windows Installer)

No Python, Git, or developer tooling required. Everything is self-contained.

1. Download **`Voice-by-SumanOnline-Setup.exe`** from the [Latest Releases](https://github.com/SumanCH8514/Voice-by-SumanOnline/releases/latest).
2. Run the installer. It installs the application, standalone Python 3.12 runtime, and desktop shortcuts.
3. Launch **Voice by SumanOnline** from your Desktop or Start Menu.
4. Press and hold **Right Alt** in any program and begin dictating.

### For Developers

Requirements:
- Windows 10 / 11 (64-bit)
- Python 3.12+
- `uv` package manager

```powershell
git clone https://github.com/SumanCH8514/Voice-by-SumanOnline.git
cd "Voice-by-SumanOnline"

uv sync

uv run python -m voice_by_sumanonline.main --ui
```

To run without opening the Voice Studio dashboard:
```powershell
uv run python -m voice_by_sumanonline.main
```

---

## Keyboard Controls

| Control | Action |
| :--- | :--- |
| **Right Alt** (Hold) | Push-to-Talk: Record voice while held, paste upon release |
| **Right Alt** (Double-Tap) | Hands-Free Mode: Tap twice rapidly to latch recording; tap once to finish and paste |
| **AltGr** | Automatically supported on European and international layouts |
| **System Tray Icon** | Access Voice Studio, toggle microphone, switch presets, or exit |

---

## Project Structure

```
├── voice_by_sumanonline/
│   ├── audio.py
│   ├── config.py
│   ├── dictionary.py
│   ├── format.py
│   ├── history.py
│   ├── hotkey.py
│   ├── hud.py
│   ├── inject.py
│   ├── keychain.py
│   ├── preview.py
│   ├── server.py
│   ├── startup.py
│   ├── transcribe.py
│   ├── tray.py
│   └── main.py
├── ui/
│   ├── src/components/
│   ├── src/services/
│   └── src/App.tsx
├── docs/
│   ├── index.html
│   └── assets/
├── installer/
│   ├── inno_setup.iss
│   └── build_installer.ps1
└── pyproject.toml
```

---

## Security & Privacy

- **Local Speech Processing**: Speech recognition runs locally on your device via Faster-Whisper. Audio waveforms never leave your machine unless cloud formatting is explicitly enabled.
- **Secure Credential Storage**: Cloud API tokens (e.g. Groq) are stored securely in the Windows Credential Manager using the OS Keychain subsystem. They are never written to disk in plain text or exposed to the frontend.
- **Cursor Focus Protection**: The floating HUD utilizes non-activating Win32 window styles (`WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST`) so your active window never drops focus during recording.

---

## Contributing

Contributions, bug reports, and suggestions are welcome.
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add amazing feature"`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">
<b>Voice by SumanOnline</b> — Built with passion by SumanOnline.
</div>
