import time
import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()


def inject_text(text):
    """Inject a single piece of text at cursor position via clipboard paste."""
    if not text:
        return
    pyperclip.copy(text)
    time.sleep(0.05)
    _keyboard.press(Key.ctrl)
    _keyboard.press("v")
    _keyboard.release("v")
    _keyboard.release(Key.ctrl)
    time.sleep(0.05)


class StreamingInjector:
    """Injects text segments one by one, preserving original clipboard."""

    def __init__(self):
        try:
            self._original_clipboard = pyperclip.paste()
        except pyperclip.PyperclipException:
            self._original_clipboard = None
        self._first = True

    def inject_segment(self, text):
        """Inject one segment. Adds a space before all segments except the first."""
        if not text:
            return
        if not self._first:
            text = " " + text
        self._first = False
        inject_text(text)

    def finish(self):
        """Restore original clipboard content."""
        time.sleep(0.1)
        if self._original_clipboard is not None:
            pyperclip.copy(self._original_clipboard)
