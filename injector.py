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
