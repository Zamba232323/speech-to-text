import sys
import ctypes
import threading
import time
from pynput import keyboard

from recorder import Recorder
from transcriber import Transcriber
from injector import inject_text
from tray import TrayApp
from cursor_indicator import CursorIndicator
from setup_check import run_checks

MUTEX_NAME = "Global\\SpeechToTextMutex_7f3a9b"
BACKGROUND_TRANSCRIBE_INTERVAL = 5  # seconds between background transcriptions


def _acquire_single_instance():
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = ctypes.get_last_error()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(mutex)
        return None
    return mutex


class SpeechToText:
    def __init__(self):
        self._recorder = Recorder()
        self._transcriber = None
        self._cursor = CursorIndicator()
        self._tray = TrayApp(
            on_setup_check=self._handle_setup_check,
            on_quit=self._handle_quit,
        )
        self._busy = False
        self._buffered_text = []
        self._bg_thread = None
        self._bg_stop = threading.Event()

    def _ensure_transcriber(self):
        if self._transcriber is None:
            self._cursor.set_transcribing()
            self._tray.set_state("transcribing")
            self._transcriber = Transcriber()
            self._cursor.set_idle()
            self._tray.set_state("idle")

    def _background_transcribe(self):
        """Periodically transcribe audio snapshots while recording."""
        while not self._bg_stop.wait(BACKGROUND_TRANSCRIBE_INTERVAL):
            if not self._recorder.is_recording:
                break
            snapshot_path = self._recorder.snapshot()
            if snapshot_path:
                self._transcriber.transcribe_streaming(
                    snapshot_path, lambda t: None  # discard, just warm cache
                )

    def _handle_hotkey(self):
        if self._busy:
            return

        if not self._recorder.is_recording:
            # === START RECORDING ===
            self._ensure_transcriber()
            self._buffered_text = []
            self._recorder.start()
            self._cursor.set_recording()
            self._tray.set_state("recording")
        else:
            # === STOP RECORDING & INJECT ===
            audio_path = self._recorder.stop()
            if audio_path is None:
                self._cursor.set_idle()
                self._tray.set_state("idle")
                return

            self._busy = True
            self._cursor.set_transcribing()
            self._tray.set_state("transcribing")

            def process():
                try:
                    segments = []
                    self._transcriber.transcribe_streaming(
                        audio_path, segments.append
                    )
                    full_text = " ".join(segments)
                    if full_text.strip():
                        inject_text(full_text.strip())
                finally:
                    self._busy = False
                    self._cursor.set_idle()
                    self._tray.set_state("idle")

            threading.Thread(target=process, daemon=True).start()

    def _handle_setup_check(self):
        threading.Thread(target=run_checks, daemon=True).start()

    def _handle_quit(self):
        if self._recorder.is_recording:
            self._recorder.stop()
        self._cursor.set_idle()
        self._tray.stop()

    def run(self):
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<ctrl>+<space>"),
            self._handle_hotkey,
        )

        def on_press(key):
            hotkey.press(self._listener.canonical(key))

        def on_release(key):
            hotkey.release(self._listener.canonical(key))

        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
        )
        self._listener.start()
        self._tray.run()


def main():
    if "--check" in sys.argv:
        run_checks()
        return

    mutex = _acquire_single_instance()
    if mutex is None:
        print("Speech-to-Text is already running.")
        sys.exit(1)

    app = SpeechToText()
    app.run()


if __name__ == "__main__":
    main()
