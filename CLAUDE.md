# Speech-to-Text — Globální klávesová zkratka pro diktování

## Co to je

Windows desktop nástroj pro diktování textu kamkoli pomocí Ctrl+Space. Nahraje řeč z mikrofonu, přepíše přes Whisper (faster-whisper) a vloží text na pozici kurzoru.

## Jak to funguje

1. **Ctrl+Space** → začne nahrávání (červené kolečko u kurzoru)
2. Mluv česky, klidně přepni okno, brouzdej...
3. **Ctrl+Space** → zastaví nahrávání, přepíše audio, vloží text tam kde je kurzor

## Struktura

Veškerý Python kód je v `src/`. Root obsahuje jen skripty a config.

- `src/stt.py` — hlavní entry point, orchestrace všech komponent
- `src/recorder.py` — nahrávání z mikrofonu (16kHz mono WAV, sounddevice)
- `src/transcriber.py` — Whisper přepis (faster-whisper, auto GPU/CPU detekce)
- `src/injector.py` — vložení textu na pozici kurzoru (clipboard + Ctrl+V)
- `src/tray.py` — system tray ikona s menu (pystray)
- `src/cursor_indicator.py` — plovoucí kolečko u kurzoru (tkinter overlay, click-through)
- `src/settings_window.py` — okno nastavení (tkinter)
- `src/setup_check.py` — diagnostika prostředí (Python, balíčky, mikrofon, CUDA)
- `src/config.py` — správa konfigurace (config.json v rootu, per-PC, gitignored)

## Klíčová rozhodnutí

- **Model:** `large-v3` na GPU, `medium` na CPU — konfigurovatelné v nastavení
- **Jazyk:** výchozí čeština, měnitelný v nastavení (cs/en/auto)
- **Hotkey:** Windows RegisterHotKey API (ne pynput — to selhávalo při přepínání oken)
- **Kurzor indikátor:** tkinter overlay okno (ne SetSystemCursor — to způsobovalo mizení kurzoru)
- **Single instance:** Windows named mutex
- **Flow:** nahrávání → přepis po zastavení → vložení textu na pozici kurzoru

## Instalace na novém PC

1. Naklonuj repo
2. Spusť `install.bat` (vysvětlí co to je, nainstaluje, nabídne autostart)
3. Spusť `start.bat` nebo restartuj PC (pokud přidáno do autostartu)

## Vývoj

- Python 3.10+
- Závislosti v `requirements.txt`
- Venv v `.venv/`
- Žádné testy (jednoduchý nástroj, testuje se ručně)
