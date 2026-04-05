import sys
import ctypes
import threading
from pynput import keyboard

from recorder import Recorder
from transcriber import Transcriber
from injector import StreamingInjector
from tray import TrayApp
from cursor_indicator import CursorIndicator
from setup_check import run_checks

MUTEX_NAME = "Global\\SpeechToTextMutex_7f3a9b"


def _acquire_single_instance():
    """Prevent multiple instances using a Windows named mutex."""
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = ctypes.get_last_error()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)
        return None
    return mutex


class SpeechToText:
    def __init__(self):
        self._recorder = Recorder()
        self._transcriber = None  # lazy-loaded
        self._cursor = CursorIndicator()
        self._tray = TrayApp(
            on_setup_check=self._handle_setup_check,
            on_quit=self._handle_quit,
        )
        self._busy = False  # True while transcribing

    def _ensure_transcriber(self):
        if self._transcriber is None:
            self._cursor.set_transcribing()
            self._tray.set_state("transcribing")
            self._transcriber = Transcriber()
            self._cursor.set_idle()
            self._tray.set_state("idle")

    def _handle_hotkey(self):
        if self._busy:
            return

        if not self._recorder.is_recording:
            # Start recording
            self._ensure_transcriber()
            self._recorder.start()
            self._cursor.set_recording()
            self._tray.set_state("recording")
        else:
            # Stop recording and transcribe
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
                    injector = StreamingInjector()
                    self._transcriber.transcribe_streaming(
                        audio_path, injector.inject_segment
                    )
                    injector.finish()
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
        # Register global hotkey Ctrl+Space
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

        # Run tray (blocks main thread)
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
