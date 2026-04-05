import tempfile
import wave
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"


class Recorder:
    def __init__(self):
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()

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
                callback=self._audio_callback,
            )
            self._stream.start()

    def stop(self):
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            self._stream.stop()
            self._stream.close()

            if not self._frames:
                return None

            # Save to temp WAV file
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(np.concatenate(self._frames).tobytes())

            self._frames = []
            return tmp.name

    def _audio_callback(self, indata, frames, time, status):
        if self._recording:
            self._frames.append(indata.copy())
