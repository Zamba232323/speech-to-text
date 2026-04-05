import json
import os
import ctypes

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

DEFAULTS = {
    "model": None,  # auto-detected
    "language": "cs",
    "hotkey_modifier": "ctrl",
    "hotkey_key": "space",
    "autostart": False,
}

# Model options with descriptions
MODELS = {
    "small": {"ram_mb": 500, "description": "Rychlý, nižší kvalita"},
    "medium": {"ram_mb": 1500, "description": "Dobrá kvalita, pomalejší na CPU"},
    "large-v3": {"ram_mb": 3000, "description": "Nejlepší kvalita, vyžaduje GPU"},
}

LANGUAGES = {
    "cs": "Čeština",
    "en": "Angličtina",
    "auto": "Automatická detekce",
}


def _has_cuda():
    try:
        ctypes.cdll.LoadLibrary("cudart64_12.dll")
        return True
    except OSError:
        return False


def get_default_config():
    defaults = dict(DEFAULTS)
    defaults["model"] = "large-v3" if _has_cuda() else "medium"
    return defaults


def load_config():
    defaults = get_default_config()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
