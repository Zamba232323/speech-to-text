# Speech-to-Text

Diktuj text kamkoli na Windows pomocí klávesové zkratky.

## Jak to funguje

1. **Ctrl+Space** → začne nahrávání (červené kolečko u kurzoru)
2. Mluv česky, klidně přepni okno, brouzdej...
3. **Ctrl+Space** → zastaví nahrávání, přepíše a vloží text tam kde je kurzor

## Instalace

```
git clone <repo-url>
cd speech-to-text
install.bat
```

Instalátor vytvoří Python venv, nainstaluje závislosti, zkontroluje prostředí a nabídne přidání do autostartu.

## Požadavky

- Windows 10 / 11
- Python 3.10+
- Mikrofon

## GPU (volitelné)

S NVIDIA GPU (CUDA) se použije model `large-v3` — nejlepší kvalita, rychlý přepis. Bez GPU běží model `medium` na CPU — dobrá kvalita, pomalejší.

## Nastavení

Pravý klik na ikonu v tray → **Nastavení**

- Změna klávesové zkratky
- Výběr modelu (small / medium / large-v3)
- Jazyk (čeština / angličtina / auto)
- Zapnutí/vypnutí autostartu
- Zobrazení spotřeby RAM a stavu

Nastavení se ukládá do `config.json` (per-PC, není v gitu).

## Spuštění

```
start.bat
```

Nebo se spustí automaticky při startu Windows (pokud povoleno v nastavení).
