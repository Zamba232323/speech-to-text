import tkinter as tk
from tkinter import ttk
import threading
import os
import psutil

from config import load_config, save_config, MODELS, LANGUAGES, _has_cuda

VERSION = "1.0.0"
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Windows hotkey modifier codes
MODIFIER_MAP = {
    "ctrl": 0x0002,
    "alt": 0x0001,
    "shift": 0x0004,
    "ctrl+shift": 0x0006,
    "ctrl+alt": 0x0003,
}

# Virtual key codes for display
VK_NAMES = {
    0x20: "Space", 0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8", 0x78: "F9",
    0x79: "F10", 0x7A: "F11", 0x7B: "F12",
}

# Reverse lookup for key names to VK codes
KEY_TO_VK = {
    "space": 0x20, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}


def _get_input_devices():
    """Return list of audio input devices."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return [d for d in devices if d["max_input_channels"] > 0]
    except Exception:
        return []


def _get_ram_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def _manage_autostart(enable):
    """Add or remove Windows Startup shortcut."""
    import subprocess
    startup_path = subprocess.check_output(
        ['powershell', '-Command', "[Environment]::GetFolderPath('Startup')"],
        text=True
    ).strip()
    shortcut_path = os.path.join(startup_path, "Speech-to-Text.lnk")

    if enable:
        start_bat = os.path.join(REPO_PATH, "start.bat")
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{start_bat}'; "
            f"$s.WorkingDirectory = '{REPO_PATH}'; "
            f"$s.WindowStyle = 7; "
            f"$s.Description = 'Speech-to-Text (Ctrl+Space)'; "
            f"$s.Save()"
        )
        subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)


class SettingsWindow:
    _instance = None

    @classmethod
    def open(cls, get_state_fn=None, on_hotkey_change_fn=None):
        """Open settings window. Singleton — focuses existing if already open."""
        if cls._instance is not None:
            try:
                cls._instance._root.focus_force()
                return
            except tk.TclError:
                cls._instance = None

        cls._instance = cls(get_state_fn, on_hotkey_change_fn)

    def __init__(self, get_state_fn, on_hotkey_change_fn):
        self._get_state = get_state_fn or (lambda: "idle")
        self._on_hotkey_change = on_hotkey_change_fn
        self._cfg = load_config()
        self._needs_restart = False

        self._root = tk.Toplevel() if tk._default_root else tk.Tk()
        self._root.title("Speech-to-Text — Nastavení")
        self._root.geometry("420x520")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self._root.attributes("-topmost", True)
        except tk.TclError:
            pass

        self._build_ui()
        self._update_status()

    def _build_ui(self):
        main = ttk.Frame(self._root, padding=15)
        main.pack(fill="both", expand=True)

        # === STATUS ===
        status_frame = ttk.LabelFrame(main, text="Status", padding=10)
        status_frame.pack(fill="x", pady=(0, 10))

        self._model_label = ttk.Label(status_frame, text="")
        self._model_label.pack(anchor="w")

        self._device_label = ttk.Label(status_frame, text="")
        self._device_label.pack(anchor="w")

        self._ram_label = ttk.Label(status_frame, text="")
        self._ram_label.pack(anchor="w")

        self._state_label = ttk.Label(status_frame, text="")
        self._state_label.pack(anchor="w")

        # === SETTINGS ===
        settings_frame = ttk.LabelFrame(main, text="Nastavení", padding=10)
        settings_frame.pack(fill="x", pady=(0, 10))

        # Hotkey
        hk_frame = ttk.Frame(settings_frame)
        hk_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(hk_frame, text="Zkratka:").pack(side="left")
        self._hotkey_label = ttk.Label(
            hk_frame,
            text=self._format_hotkey(),
            font=("Consolas", 10, "bold"),
        )
        self._hotkey_label.pack(side="left", padx=(8, 8))
        self._hotkey_btn = ttk.Button(hk_frame, text="Změnit", command=self._start_hotkey_capture)
        self._hotkey_btn.pack(side="left")

        # Model
        model_frame = ttk.Frame(settings_frame)
        model_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(model_frame, text="Model:").pack(side="left")
        self._model_var = tk.StringVar(value=self._cfg["model"])
        model_combo = ttk.Combobox(
            model_frame, textvariable=self._model_var,
            values=list(MODELS.keys()), state="readonly", width=12,
        )
        model_combo.pack(side="left", padx=(8, 8))
        model_combo.bind("<<ComboboxSelected>>", self._on_model_change)

        self._model_desc = ttk.Label(model_frame, text=MODELS[self._cfg["model"]]["description"])
        self._model_desc.pack(side="left")

        # Microphone
        mic_frame = ttk.Frame(settings_frame)
        mic_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(mic_frame, text="Mikrofon:").pack(side="left")
        self._mic_devices = _get_input_devices()
        mic_names = [d["name"] for d in self._mic_devices]
        current_mic = self._cfg.get("microphone", "")
        if current_mic not in mic_names and mic_names:
            current_mic = mic_names[0]
        self._mic_var = tk.StringVar(value=current_mic)
        mic_combo = ttk.Combobox(
            mic_frame, textvariable=self._mic_var,
            values=mic_names, state="readonly", width=35,
        )
        mic_combo.pack(side="left", padx=(8, 0))
        mic_combo.bind("<<ComboboxSelected>>", self._on_mic_change)

        # Language
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(lang_frame, text="Jazyk:").pack(side="left")
        self._lang_var = tk.StringVar(value=self._cfg["language"])
        lang_combo = ttk.Combobox(
            lang_frame, textvariable=self._lang_var,
            values=list(LANGUAGES.keys()), state="readonly", width=12,
        )
        lang_combo.pack(side="left", padx=(8, 0))

        # Show language display names
        lang_display = ttk.Label(lang_frame, text=LANGUAGES[self._cfg["language"]])
        lang_display.pack(side="left", padx=(8, 0))
        self._lang_display = lang_display
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._on_lang_change(e))

        # Autostart
        self._autostart_var = tk.BooleanVar(value=self._cfg.get("autostart", False))
        autostart_cb = ttk.Checkbutton(
            settings_frame, text="Spustit při startu Windows",
            variable=self._autostart_var, command=self._on_autostart_toggle,
        )
        autostart_cb.pack(anchor="w", pady=(0, 4))

        # Restart warning + button
        self._restart_frame = ttk.Frame(settings_frame)
        self._restart_label = ttk.Label(
            self._restart_frame, text="⚠ Vyžaduje restart",
            foreground="orange",
        )
        self._restart_label.pack(side="left")
        self._restart_btn = ttk.Button(
            self._restart_frame, text="Restartovat", command=self._restart_app,
        )
        self._restart_btn.pack(side="left", padx=(10, 0))

        # === INFO ===
        info_frame = ttk.LabelFrame(main, text="Info", padding=10)
        info_frame.pack(fill="x")

        ttk.Label(info_frame, text=f"Verze: {VERSION}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Cesta: {REPO_PATH}").pack(anchor="w")

        btn_frame = ttk.Frame(info_frame)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="Setup Check", command=self._run_setup_check).pack(side="left")

    def _format_hotkey(self):
        mod = self._cfg.get("hotkey_modifier", "ctrl").capitalize()
        key = self._cfg.get("hotkey_key", "space").capitalize()
        return f"{mod}+{key}"

    def _update_status(self):
        try:
            self._model_label.config(text=f"Model: {self._cfg['model']}")
            device = "CUDA (GPU)" if _has_cuda() else "CPU"
            self._device_label.config(text=f"Zařízení: {device}")
            ram = _get_ram_mb()
            self._ram_label.config(text=f"RAM: {ram:.0f} MB")
            state_names = {"idle": "Připraven", "recording": "Nahrávám", "transcribing": "Přepisuji"}
            state = self._get_state()
            self._state_label.config(text=f"Stav: {state_names.get(state, state)}")
            self._root.after(2000, self._update_status)
        except tk.TclError:
            pass

    def _start_hotkey_capture(self):
        self._hotkey_btn.config(text="Stiskni zkratku...", state="disabled")
        self._hotkey_label.config(text="...")
        self._root.bind("<Key>", self._capture_hotkey)

    def _capture_hotkey(self, event):
        self._root.unbind("<Key>")

        mod_parts = []
        if event.state & 0x4:  # Control
            mod_parts.append("ctrl")
        if event.state & 0x1:  # Shift
            mod_parts.append("shift")
        if event.state & 0x20000:  # Alt
            mod_parts.append("alt")

        if not mod_parts:
            # Need at least one modifier
            self._hotkey_btn.config(text="Změnit", state="normal")
            self._hotkey_label.config(text=self._format_hotkey())
            return

        modifier = "+".join(mod_parts)
        key_name = event.keysym.lower()

        # Map common key names
        key_map = {"space": "space", "return": "return", "escape": "escape"}
        for i in range(1, 13):
            key_map[f"f{i}"] = f"f{i}"

        if key_name in ("control_l", "control_r", "shift_l", "shift_r", "alt_l", "alt_r"):
            # Just a modifier, wait for the actual key
            self._root.bind("<Key>", self._capture_hotkey)
            return

        key = key_map.get(key_name, key_name)

        self._cfg["hotkey_modifier"] = modifier
        self._cfg["hotkey_key"] = key
        save_config(self._cfg)

        self._hotkey_label.config(text=self._format_hotkey())
        self._hotkey_btn.config(text="Změnit", state="normal")

        if self._on_hotkey_change:
            self._on_hotkey_change(modifier, key)

        self._show_restart_warning()

    def _on_model_change(self, event=None):
        model = self._model_var.get()
        self._cfg["model"] = model
        self._model_desc.config(text=MODELS[model]["description"])
        save_config(self._cfg)
        self._show_restart_warning()

    def _on_mic_change(self, event=None):
        mic_name = self._mic_var.get()
        self._cfg["microphone"] = mic_name
        save_config(self._cfg)
        self._show_restart_warning()

    def _on_lang_change(self, event=None):
        lang = self._lang_var.get()
        self._cfg["language"] = lang
        self._lang_display.config(text=LANGUAGES[lang])
        save_config(self._cfg)
        self._show_restart_warning()

    def _on_autostart_toggle(self):
        enabled = self._autostart_var.get()
        self._cfg["autostart"] = enabled
        save_config(self._cfg)
        threading.Thread(
            target=_manage_autostart, args=(enabled,), daemon=True
        ).start()

    def _show_restart_warning(self):
        self._restart_frame.pack(anchor="w", pady=(4, 0))

    def _restart_app(self):
        """Restart the application by launching a new instance and quitting."""
        import subprocess
        import sys
        start_bat = os.path.join(REPO_PATH, "start.bat")
        subprocess.Popen(["cmd", "/c", start_bat], cwd=REPO_PATH)
        # Quit current instance
        self._on_close()
        os._exit(0)

    def _run_setup_check(self):
        from setup_check import run_checks
        threading.Thread(target=run_checks, daemon=True).start()

    def _on_close(self):
        SettingsWindow._instance = None
        self._root.destroy()
