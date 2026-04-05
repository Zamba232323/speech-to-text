# Settings Window Design

## Overview

Right-click tray icon → "Settings" opens a tkinter settings window. Shows status, allows configuration of model, hotkey, language, autostart. Config persisted in `config.json` (gitignored, per-PC).

## Settings Window Layout

Three sections in a single tkinter Toplevel window (~400x500px):

### Status Section
- **Model:** current model name (e.g. `large-v3`, `medium`)
- **Device:** `CUDA` or `CPU`
- **RAM:** current process memory usage in MB
- **State:** Idle / Recording / Transcribing (live-updated)

### Settings Section
- **Hotkey:** shows current shortcut (e.g. `Ctrl+Space`), button "Change" → captures next key combo
- **Model:** dropdown (`small`, `medium`, `large-v3`) — shows warning about RAM/speed tradeoffs. Change requires restart.
- **Language:** dropdown (`cs` Czech, `en` English, `auto` detect)
- **Autostart:** checkbox — adds/removes Windows Startup shortcut

### Info Section
- App version
- Repo path
- "Run Setup Check" button

## Config File: config.json

Located in repo root, gitignored. Schema:

```json
{
  "model": "medium",
  "language": "cs",
  "hotkey_modifier": "ctrl",
  "hotkey_key": "space",
  "autostart": true
}
```

Defaults if config.json doesn't exist:
- model: `large-v3` if CUDA, `medium` if CPU
- language: `cs`
- hotkey: `Ctrl+Space`
- autostart: false

## New/Modified Files

- Create: `config.py` — load/save config, defaults, schema
- Create: `settings_window.py` — tkinter settings UI
- Modify: `tray.py` — add "Settings" menu item
- Modify: `stt.py` — use config for model/hotkey/language, pass state to settings
- Modify: `transcriber.py` — accept model/language from config instead of hardcoded
- Modify: `.gitignore` — add `config.json`

## Behavior

- Settings window is a singleton (one instance at a time)
- Model/language changes show "Restart required" label
- Hotkey change: click "Change" → button text becomes "Press new shortcut..." → captures combo → unregisters old, registers new
- Autostart toggle: immediately adds/removes Startup shortcut
- RAM display updates every 2 seconds while window is open
- State display updates in real-time
