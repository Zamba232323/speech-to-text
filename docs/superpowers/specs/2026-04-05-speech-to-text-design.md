# Speech-to-Text Global Hotkey Tool

## Overview

Desktop tool for Windows 10/11 that enables speech-to-text input anywhere via a global keyboard shortcut. Press Ctrl+Space to start recording, press again to stop — transcribed text is injected at the cursor position in any application.

Designed as a portable repo to clone and run on multiple PCs with varying hardware (some with NVIDIA GPU, some CPU-only).

## Architecture

```
speech-to-text/
├── stt.py              # main entry point, orchestrates components
├── recorder.py         # microphone recording (sounddevice)
├── transcriber.py      # Whisper transcription (faster-whisper)
├── injector.py         # text injection at cursor position
├── tray.py             # system tray icon and menu
├── setup_check.py      # environment diagnostics
├── requirements.txt
├── install.bat         # one-time setup: venv + deps + check
└── start.bat           # launch the app
```

## Components

### recorder.py — Microphone Recording

- Uses `sounddevice` library (bundled PortAudio, no system deps)
- Records at 16kHz mono (Whisper's expected format)
- Saves to temp WAV file, deleted after transcription
- Graceful handling if no microphone detected (tray notification, no crash)

### transcriber.py — Whisper Transcription

- Uses `faster-whisper` (CTranslate2 backend, 2-4x faster than original Whisper)
- Model selection based on hardware:
  - **GPU available (CUDA):** `medium` model — best quality/speed ratio for Czech
  - **CPU only:** `small` model — good quality, reasonable speed
- Model loaded once at startup, stays in memory for fast subsequent transcriptions
- Language hardcoded to `cs` (Czech) — no autodetection, faster and more accurate
- Filters out hallucinated/empty segments (common with silence)

### injector.py — Text Injection

- Copies transcribed text to clipboard
- Simulates Ctrl+V via `pynput` to paste at current cursor position
- Restores original clipboard content after injection

### tray.py — System Tray

- Uses `pystray` with programmatically generated icons (no external image files)
- Three states:
  - **Grey microphone** — idle, ready to record
  - **Red microphone** — recording in progress
  - **Yellow microphone** — transcribing
- Right-click menu: "Setup check", "Quit"
- App starts directly into tray, no window

### setup_check.py — Environment Diagnostics

Runs at first launch and on-demand from tray menu. Checks:

- Python version (>= 3.10)
- All pip packages installed correctly
- Microphone availability and access
- CUDA / GPU detection (cuDNN, CUDA toolkit)
- Whisper model downloaded

Outputs a clear report: what's OK, what's missing, and how to fix it.

## Global Hotkey

- `pynput` keyboard listener in a separate thread
- **Ctrl+Space** toggles recording start/stop
- Works across all applications (browsers, editors, terminals, etc.)
- Ctrl+Space is ignored while transcription is in progress (yellow state)

## Data Flow

```
Ctrl+Space (start)
    → recorder starts capturing audio
Ctrl+Space (stop)
    → recorder saves WAV to temp file
    → transcriber runs faster-whisper on WAV
    → injector copies text to clipboard
    → injector simulates Ctrl+V
    → injector restores original clipboard
    → temp WAV deleted
```

## Dependencies

```
faster-whisper      # Whisper CTranslate2 — fast transcription
sounddevice         # microphone recording
numpy               # required by sounddevice
pynput              # global hotkey + key simulation
pystray             # system tray icon
Pillow              # icon generation for tray
pyperclip           # clipboard operations
```

CUDA support is optional — `faster-whisper` auto-detects CUDA if cuDNN and CUDA toolkit are installed. `setup_check.py` verifies this and advises on installation if missing.

No C compilers or additional system libraries required.

## Setup Scripts

### install.bat

1. Creates Python venv in `.venv/`
2. Installs dependencies from `requirements.txt`
3. Runs `setup_check.py` automatically
4. Reports whether GPU acceleration is available

### start.bat

1. Activates venv
2. Launches `stt.py`
3. Optional `--autostart` flag to add to Windows Startup

## Target Environment

- **OS:** Windows 10 and Windows 11
- **Python:** 3.10+
- **GPU:** Optional NVIDIA with CUDA (auto-detected)
- **Language:** Czech (`cs`)
- **Repo location:** `A:\cursor\speech-to-text` (cloned to each PC)
