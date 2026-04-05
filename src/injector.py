import time
import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()


def inject_text(text):
    """Inject text at cursor position via clipboard paste."""
    if not text:
        return

    try:
        original_clipboard = pyperclip.paste()
    except pyperclip.PyperclipException:
        original_clipboard = None

    pyperclip.copy(text)
    time.sleep(0.05)

    _keyboard.press(Key.ctrl)
    _keyboard.press("v")
    _keyboard.release("v")
    _keyboard.release(Key.ctrl)

    time.sleep(0.1)
    if original_clipboard is not None:
        pyperclip.copy(original_clipboard)
