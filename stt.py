import sys
import ctypes
import ctypes.wintypes
import threading

from recorder import Recorder
from transcriber import Transcriber
from injector import inject_text
from tray import TrayApp
from cursor_indicator import CursorIndicator
from setup_check import run_checks

MUTEX_NAME = "Global\\SpeechToTextMutex_7f3a9b"

user32 = ctypes.windll.user32

# Windows hotkey constants
MOD_CONTROL = 0x0002
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
HOTKEY_ID = 1


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
            # === START RECORDING ===
            self._ensure_transcriber()
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
        # Unregister hotkey before stopping
        user32.UnregisterHotKey(None, HOTKEY_ID)
        self._tray.stop()

    def _hotkey_listener(self):
        """Windows message loop for global hotkey — runs in its own thread."""
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL, VK_SPACE):
            print("ERROR: Could not register Ctrl+Space hotkey. Is another instance running?")
            return

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._handle_hotkey()

    def run(self):
        # Start hotkey listener in background thread
        hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        hotkey_thread.start()

        # Run tray in main thread (blocks)
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
