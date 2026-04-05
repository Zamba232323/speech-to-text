import tempfile
import wave
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"


class Recorder:
    def __init__(self, device=None):
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()
        self._device = device

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                device=self._device,
                callback=self._audio_callback,
            )
            self._stream.start()

    def snapshot(self):
        """Return a WAV file of audio recorded so far, without stopping."""
        with self._lock:
            if not self._frames:
                return None
            return self._save_frames(list(self._frames))

    def stop(self):
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            self._stream.stop()
            self._stream.close()

            if not self._frames:
                return None

            path = self._save_frames(self._frames)
            self._frames = []
            return path

    def _save_frames(self, frames):
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(np.concatenate(frames).tobytes())
        return tmp.name

    def _audio_callback(self, indata, frames, time, status):
        if self._recording:
            self._frames.append(indata.copy())
