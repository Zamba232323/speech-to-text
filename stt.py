import sys
import threading
from pynput import keyboard

from recorder import Recorder
from transcriber import Transcriber
from injector import inject_text
from tray import TrayApp
from setup_check import run_checks


class SpeechToText:
    def __init__(self):
        self._recorder = Recorder()
        self._transcriber = None  # lazy-loaded
        self._tray = TrayApp(
            on_setup_check=self._handle_setup_check,
            on_quit=self._handle_quit,
        )
        self._busy = False  # True while transcribing

    def _ensure_transcriber(self):
        if self._transcriber is None:
            self._tray.set_state("transcribing")
            self._transcriber = Transcriber()
            self._tray.set_state("idle")

    def _handle_hotkey(self):
        if self._busy:
            return

        if not self._recorder.is_recording:
            # Start recording
            self._ensure_transcriber()
            self._recorder.start()
            self._tray.set_state("recording")
        else:
            # Stop recording and transcribe
            audio_path = self._recorder.stop()
            if audio_path is None:
                self._tray.set_state("idle")
                return

            self._busy = True
            self._tray.set_state("transcribing")

            def process():
                try:
                    text = self._transcriber.transcribe(audio_path)
                    if text:
                        inject_text(text)
                finally:
                    self._busy = False
                    self._tray.set_state("idle")

            threading.Thread(target=process, daemon=True).start()

    def _handle_setup_check(self):
        threading.Thread(target=run_checks, daemon=True).start()

    def _handle_quit(self):
        if self._recorder.is_recording:
            self._recorder.stop()
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

    app = SpeechToText()
    app.run()


if __name__ == "__main__":
    main()
