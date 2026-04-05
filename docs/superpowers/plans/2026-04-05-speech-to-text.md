# Speech-to-Text Global Hotkey — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows tray app that records speech via Ctrl+Space and injects transcribed Czech text at the cursor position using faster-whisper.

**Architecture:** Six focused Python modules (recorder, transcriber, injector, tray, setup_check, stt) plus two .bat scripts for install/launch. Each module has one responsibility and communicates through simple function calls. The main `stt.py` wires them together.

**Tech Stack:** Python 3.10+, faster-whisper, sounddevice, pynput, pystray, Pillow, pyperclip

---

### Task 1: Project scaffold — requirements.txt, install.bat, start.bat

**Files:**
- Create: `requirements.txt`
- Create: `install.bat`
- Create: `start.bat`
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```gitignore
.venv/
__pycache__/
*.pyc
*.wav
*.tmp
```

- [ ] **Step 2: Create requirements.txt**

```
faster-whisper>=1.0.0
sounddevice>=0.4.6
numpy>=1.24.0
pynput>=1.7.6
pystray>=0.19.5
Pillow>=10.0.0
pyperclip>=1.8.2
```

- [ ] **Step 3: Create install.bat**

```bat
@echo off
echo === Speech-to-Text Installer ===
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Running setup check...
python setup_check.py

echo.
echo === Installation complete ===
pause
```

- [ ] **Step 4: Create start.bat**

```bat
@echo off
call "%~dp0.venv\Scripts\activate.bat"
pythonw "%~dp0stt.py" %*
```

Note: `pythonw` runs without a console window. `%~dp0` ensures paths work regardless of working directory.

- [ ] **Step 5: Commit**

```bash
git add .gitignore requirements.txt install.bat start.bat
git commit -m "feat: add project scaffold — requirements, install, start scripts"
```

---

### Task 2: setup_check.py — Environment diagnostics

**Files:**
- Create: `setup_check.py`

- [ ] **Step 1: Create setup_check.py**

```python
import sys
import shutil
import subprocess


def check_python_version():
    v = sys.version_info
    ok = v >= (3, 10)
    ver = f"{v.major}.{v.minor}.{v.micro}"
    return ok, f"Python {ver}", "" if ok else "Install Python 3.10+ from python.org"


def check_package(name):
    try:
        __import__(name)
        return True, f"{name} installed", ""
    except ImportError:
        return False, f"{name} MISSING", f"Run: pip install {name}"


def check_microphone():
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d["max_input_channels"] > 0]
        if input_devices:
            default = sd.query_devices(kind="input")
            return True, f"Microphone: {default['name']}", ""
        return False, "No microphone found", "Connect a microphone and retry"
    except Exception as e:
        return False, f"Microphone error: {e}", "Check audio drivers"


def check_cuda():
    try:
        import ctypes
        ctypes.cdll.LoadLibrary("cudart64_12.dll")
        return True, "CUDA available — will use 'medium' model", ""
    except OSError:
        return False, "CUDA not available — will use 'small' model (CPU)", (
            "Optional: Install CUDA toolkit + cuDNN for faster transcription"
        )


def check_whisper_model():
    try:
        from faster_whisper.utils import download_model
        import os
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
        # Just check if faster_whisper can be imported; model downloads on first use
        return True, "faster-whisper ready (model downloads on first run)", ""
    except ImportError:
        return False, "faster-whisper not installed", "Run: pip install faster-whisper"


def run_checks():
    checks = [
        check_python_version(),
        check_package("faster_whisper"),
        check_package("sounddevice"),
        check_package("pynput"),
        check_package("pystray"),
        check_package("PIL"),
        check_package("pyperclip"),
        check_microphone(),
        check_cuda(),
        check_whisper_model(),
    ]

    print("=" * 50)
    print("  Speech-to-Text Setup Check")
    print("=" * 50)
    print()

    all_ok = True
    for ok, message, fix in checks:
        status = "[OK]  " if ok else "[FAIL]"
        print(f"  {status} {message}")
        if not ok and fix:
            print(f"         -> {fix}")
            all_ok = False

    print()
    if all_ok:
        print("  All checks passed! Run start.bat to launch.")
    else:
        print("  Some checks failed. Fix the issues above and re-run.")
    print()
    return all_ok


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
```

- [ ] **Step 2: Run setup_check.py to verify it works**

Run: `cd /a/cursor/speech-to-text && python setup_check.py`
Expected: Output showing check results (packages will show FAIL since no venv yet — that's correct)

- [ ] **Step 3: Commit**

```bash
git add setup_check.py
git commit -m "feat: add environment diagnostics (setup_check.py)"
```

---

### Task 3: recorder.py — Microphone recording

**Files:**
- Create: `recorder.py`

- [ ] **Step 1: Create recorder.py**

```python
import tempfile
import wave
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"


class Recorder:
    def __init__(self):
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._audio_callback,
            )
            self._stream.start()

    def stop(self):
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            self._stream.stop()
            self._stream.close()

            if not self._frames:
                return None

            # Save to temp WAV file
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(np.concatenate(self._frames).tobytes())

            self._frames = []
            return tmp.name

    def _audio_callback(self, indata, frames, time, status):
        if self._recording:
            self._frames.append(indata.copy())
```

- [ ] **Step 2: Quick manual test**

Run: `cd /a/cursor/speech-to-text && python -c "from recorder import Recorder; r = Recorder(); print('Recorder imports OK')"`
Expected: `Recorder imports OK`

- [ ] **Step 3: Commit**

```bash
git add recorder.py
git commit -m "feat: add microphone recorder (16kHz mono WAV)"
```

---

### Task 4: transcriber.py — Whisper transcription

**Files:**
- Create: `transcriber.py`

- [ ] **Step 1: Create transcriber.py**

```python
import os
import ctypes
from faster_whisper import WhisperModel

LANGUAGE = "cs"


def _has_cuda():
    try:
        ctypes.cdll.LoadLibrary("cudart64_12.dll")
        return True
    except OSError:
        return False


class Transcriber:
    def __init__(self):
        if _has_cuda():
            self._model_size = "medium"
            self._device = "cuda"
            self._compute_type = "float16"
        else:
            self._model_size = "small"
            self._device = "cpu"
            self._compute_type = "int8"

        print(f"Loading Whisper model '{self._model_size}' on {self._device}...")
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        print("Model loaded.")

    @property
    def model_size(self):
        return self._model_size

    @property
    def device(self):
        return self._device

    def transcribe(self, audio_path):
        segments, info = self._model.transcribe(
            audio_path,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,
        )

        texts = []
        for segment in segments:
            text = segment.text.strip()
            # Filter hallucinated/empty segments
            if not text:
                continue
            # Whisper sometimes repeats the same phrase on silence
            if texts and text == texts[-1]:
                continue
            texts.append(text)

        # Clean up temp file
        try:
            os.remove(audio_path)
        except OSError:
            pass

        return " ".join(texts)
```

- [ ] **Step 2: Quick import test**

Run: `cd /a/cursor/speech-to-text && python -c "from transcriber import Transcriber; print('Transcriber imports OK')"`
Expected: `Transcriber imports OK` (will also print model loading — first run downloads the model)

- [ ] **Step 3: Commit**

```bash
git add transcriber.py
git commit -m "feat: add Whisper transcriber with auto GPU/CPU detection"
```

---

### Task 5: injector.py — Text injection at cursor

**Files:**
- Create: `injector.py`

- [ ] **Step 1: Create injector.py**

```python
import time
import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()


def inject_text(text):
    if not text:
        return

    # Save current clipboard
    try:
        original_clipboard = pyperclip.paste()
    except pyperclip.PyperclipException:
        original_clipboard = None

    # Copy transcribed text to clipboard
    pyperclip.copy(text)

    # Small delay to ensure clipboard is ready
    time.sleep(0.05)

    # Simulate Ctrl+V
    _keyboard.press(Key.ctrl)
    _keyboard.press("v")
    _keyboard.release("v")
    _keyboard.release(Key.ctrl)

    # Wait for paste to complete, then restore clipboard
    time.sleep(0.1)
    if original_clipboard is not None:
        pyperclip.copy(original_clipboard)
```

- [ ] **Step 2: Quick import test**

Run: `cd /a/cursor/speech-to-text && python -c "from injector import inject_text; print('Injector imports OK')"`
Expected: `Injector imports OK`

- [ ] **Step 3: Commit**

```bash
git add injector.py
git commit -m "feat: add text injector (clipboard + Ctrl+V simulation)"
```

---

### Task 6: tray.py — System tray icon

**Files:**
- Create: `tray.py`

- [ ] **Step 1: Create tray.py**

```python
import threading
from PIL import Image, ImageDraw
import pystray


# Icon colors for each state
COLORS = {
    "idle": "#888888",       # grey
    "recording": "#FF0000",  # red
    "transcribing": "#FFD700",  # yellow
}


def _create_icon_image(color):
    """Generate a 64x64 microphone icon with the given color."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Microphone body (rounded rectangle approximation)
    draw.rounded_rectangle([20, 8, 44, 36], radius=8, fill=color)

    # Microphone stand arc
    draw.arc([16, 20, 48, 48], start=0, end=180, fill=color, width=3)

    # Stand line
    draw.line([32, 48, 32, 56], fill=color, width=3)

    # Base
    draw.line([24, 56, 40, 56], fill=color, width=3)

    return img


class TrayApp:
    def __init__(self, on_setup_check, on_quit):
        self._state = "idle"
        self._on_setup_check = on_setup_check
        self._on_quit = on_quit
        self._icon = None

    def set_state(self, state):
        """Update tray icon state: 'idle', 'recording', or 'transcribing'."""
        self._state = state
        if self._icon:
            self._icon.icon = _create_icon_image(COLORS[state])
            tooltips = {
                "idle": "Speech-to-Text — Ready (Ctrl+Space)",
                "recording": "Speech-to-Text — Recording...",
                "transcribing": "Speech-to-Text — Transcribing...",
            }
            self._icon.title = tooltips[state]

    def run(self):
        """Start the tray icon. Blocks the calling thread."""
        menu = pystray.Menu(
            pystray.MenuItem("Setup Check", lambda: self._on_setup_check()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self._on_quit()),
        )

        self._icon = pystray.Icon(
            name="speech-to-text",
            icon=_create_icon_image(COLORS["idle"]),
            title="Speech-to-Text — Ready (Ctrl+Space)",
            menu=menu,
        )
        self._icon.run()

    def stop(self):
        if self._icon:
            self._icon.stop()
```

- [ ] **Step 2: Quick import test**

Run: `cd /a/cursor/speech-to-text && python -c "from tray import TrayApp; print('TrayApp imports OK')"`
Expected: `TrayApp imports OK`

- [ ] **Step 3: Commit**

```bash
git add tray.py
git commit -m "feat: add system tray icon with state colors (idle/recording/transcribing)"
```

---

### Task 7: stt.py — Main entry point, wire everything together

**Files:**
- Create: `stt.py`

- [ ] **Step 1: Create stt.py**

```python
import sys
import threading
from pynput import keyboard

from recorder import Recorder
from transcriber import Transcriber
from injector import inject_text
from tray import TrayApp
from setup_check import run_checks


class SpeechToText:
    def __init__(self):
        self._recorder = Recorder()
        self._transcriber = None  # lazy-loaded
        self._tray = TrayApp(
            on_setup_check=self._handle_setup_check,
            on_quit=self._handle_quit,
        )
        self._busy = False  # True while transcribing

    def _ensure_transcriber(self):
        if self._transcriber is None:
            self._tray.set_state("transcribing")
            self._transcriber = Transcriber()
            self._tray.set_state("idle")

    def _handle_hotkey(self):
        if self._busy:
            return

        if not self._recorder.is_recording:
            # Start recording
            self._ensure_transcriber()
            self._recorder.start()
            self._tray.set_state("recording")
        else:
            # Stop recording and transcribe
            audio_path = self._recorder.stop()
            if audio_path is None:
                self._tray.set_state("idle")
                return

            self._busy = True
            self._tray.set_state("transcribing")

            def process():
                try:
                    text = self._transcriber.transcribe(audio_path)
                    if text:
                        inject_text(text)
                finally:
                    self._busy = False
                    self._tray.set_state("idle")

            threading.Thread(target=process, daemon=True).start()

    def _handle_setup_check(self):
        threading.Thread(target=run_checks, daemon=True).start()

    def _handle_quit(self):
        if self._recorder.is_recording:
            self._recorder.stop()
        self._tray.stop()

    def run(self):
        # Register global hotkey Ctrl+Space
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<ctrl>+<space>"),
            self._handle_hotkey,
        )

        def on_press(key):
            hotkey.press(self._listener.canonical(key))

        def on_release(key):
            hotkey.release(self._listener.canonical(key))

        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
        )
        self._listener.start()

        # Run tray (blocks main thread)
        self._tray.run()


def main():
    if "--check" in sys.argv:
        run_checks()
        return

    app = SpeechToText()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

Run: `cd /a/cursor/speech-to-text && python -c "import py_compile; py_compile.compile('stt.py', doraise=True); print('stt.py syntax OK')"`
Expected: `stt.py syntax OK`

- [ ] **Step 3: Commit**

```bash
git add stt.py
git commit -m "feat: add main entry point — wires recorder, transcriber, tray, hotkey"
```

---

### Task 8: End-to-end manual test

- [ ] **Step 1: Install dependencies in venv**

Run:
```bash
cd /a/cursor/speech-to-text
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```
Expected: All packages install successfully

- [ ] **Step 2: Run setup check**

Run: `cd /a/cursor/speech-to-text && .venv/Scripts/python setup_check.py`
Expected: Check output showing status of all components

- [ ] **Step 3: Launch the app**

Run: `cd /a/cursor/speech-to-text && .venv/Scripts/pythonw stt.py`
Expected: Tray icon appears (grey microphone)

- [ ] **Step 4: Test the full flow**

1. Press Ctrl+Space — tray icon turns red (recording)
2. Speak a Czech sentence
3. Press Ctrl+Space — tray icon turns yellow (transcribing), then grey (idle)
4. Verify transcribed text appears at cursor position

- [ ] **Step 5: Test tray menu**

1. Right-click tray icon
2. Click "Setup Check" — verify it runs diagnostics
3. Click "Quit" — verify app exits cleanly

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: verify end-to-end flow works"
```
