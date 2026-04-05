# Speech-to-Text

Diktuj text kamkoli na Windows pomocí klávesové zkratky.

## Jak to funguje

1. **Ctrl+Space** → začne nahrávání (červené kolečko u kurzoru)
2. Mluv česky, klidně přepni okno, brouzdej...
3. **Ctrl+Space** → zastaví nahrávání, přepíše a vloží text tam kde je kurzor

```mermaid
flowchart LR
    A["🎤 Ctrl+Space\n(start)"] --> B["Nahrávání\n🔴 červené kolečko"]
    B --> C["🎤 Ctrl+Space\n(stop)"]
    C --> D["Whisper přepis\n🟡 žluté kolečko"]
    D --> E["📋 Text vložen\nna pozici kurzoru"]
```

## Struktura

```
speech-to-text/
├── src/
│   ├── stt.py                # hlavní entry point
│   ├── recorder.py           # nahrávání z mikrofonu
│   ├── transcriber.py        # Whisper přepis (faster-whisper)
│   ├── injector.py           # vložení textu na pozici kurzoru
│   ├── tray.py               # system tray ikona
│   ├── cursor_indicator.py   # plovoucí indikátor u kurzoru
│   ├── settings_window.py    # okno nastavení
│   ├── setup_check.py        # diagnostika prostředí
│   └── config.py             # správa konfigurace
├── install.bat               # instalace + autostart
├── start.bat                 # spuštění aplikace
├── requirements.txt
└── README.md
```

## Architektura

```mermaid
flowchart TB
    subgraph Tray["System Tray"]
        TrayIcon["tray.py\nikona + menu"]
    end

    subgraph Core["Jádro"]
        STT["stt.py\norchestrace"]
        REC["recorder.py\n16kHz mono"]
        TRANS["transcriber.py\nfaster-whisper"]
        INJ["injector.py\nclipboard + Ctrl+V"]
    end

    subgraph UI["Indikátory"]
        CURSOR["cursor_indicator.py\nplovoucí kolečko"]
        SETTINGS["settings_window.py\ntkinter okno"]
    end

    subgraph Config["Konfigurace"]
        CFG["config.py"]
        JSON["config.json\nper-PC"]
    end

    STT --> REC
    STT --> TRANS
    STT --> INJ
    STT --> TrayIcon
    STT --> CURSOR
    TrayIcon --> SETTINGS
    SETTINGS --> CFG
    CFG --> JSON
    STT --> CFG

    HOTKEY["⌨️ RegisterHotKey\nCtrl+Space"] --> STT
```

## Instalace

```
git clone https://github.com/Zamba232323/speech-to-text.git
cd speech-to-text
install.bat
```

Instalátor:
1. Zkontroluje Python 3.10+
2. Vytvoří virtuální prostředí
3. Nainstaluje závislosti
4. Spustí diagnostiku (mikrofon, GPU, balíčky)
5. Nabídne přidání do autostartu

## GPU

| GPU | Model | Kvalita | Rychlost |
|-----|-------|---------|----------|
| NVIDIA (CUDA) | `large-v3` | nejlepší | ~2-3s |
| Bez GPU | `medium` | dobrá | ~15-20s |

## Nastavení

Pravý klik na ikonu v tray → **Nastavení**

- Klávesová zkratka (výchozí Ctrl+Space)
- Model (small / medium / large-v3)
- Jazyk (čeština / angličtina / auto)
- Autostart (zapnout / vypnout)
- Zobrazení RAM, stavu, zařízení
