# Speech-to-Text — Globální klávesová zkratka pro diktování

## Co to je

Windows desktop nástroj pro diktování textu kamkoli pomocí Ctrl+Space. Nahraje řeč z mikrofonu, přepíše přes Whisper (faster-whisper) a vloží text na pozici kurzoru.

## Jak to funguje

1. **Ctrl+Space** → začne nahrávání (červené kolečko u kurzoru)
2. Mluv česky, klidně přepni okno, brouzdej...
3. **Ctrl+Space** → zastaví nahrávání, přepíše audio, vloží text tam kde je kurzor

## Architektura

- `stt.py` — hlavní entry point, orchestrace všech komponent
- `recorder.py` — nahrávání z mikrofonu (16kHz mono WAV, sounddevice)
- `transcriber.py` — Whisper přepis (faster-whisper, auto GPU/CPU detekce)
- `injector.py` — vložení textu na pozici kurzoru (clipboard + Ctrl+V)
- `tray.py` — system tray ikona s menu (pystray)
- `cursor_indicator.py` — plovoucí kolečko u kurzoru (tkinter overlay, click-through)
- `setup_check.py` — diagnostika prostředí (Python, balíčky, mikrofon, CUDA)
- `install.bat` — instalace: venv + deps + setup check + nabídka autostartu
- `start.bat` — spuštění aplikace

## Klíčová rozhodnutí

- **Jazyk přepisu:** čeština (`cs`), hardcoded
- **Model:** `medium` vždy (i na CPU), kvalita > rychlost
- **Hotkey:** Windows RegisterHotKey API (ne pynput — to selhávalo při přepínání oken)
- **Kurzor indikátor:** tkinter overlay okno (ne SetSystemCursor — to způsobovalo mizení kurzoru)
- **Single instance:** Windows named mutex
- **Flow:** nahrávání → přepis na pozadí → vložení textu až při zastavení (ne průběžně)

## Instalace na novém PC

1. Naklonuj repo
2. Spusť `install.bat` (vysvětlí co to je, nainstaluje, nabídne autostart)
3. Spusť `start.bat` nebo restartuj PC (pokud přidáno do autostartu)

## Vývoj

- Python 3.10+
- Závislosti v `requirements.txt`
- Venv v `.venv/`
- Žádné testy (jednoduchý nástroj, testuje se ručně)
