import os
import ctypes
from faster_whisper import WhisperModel

LANGUAGE = "cs"
INITIAL_PROMPT = "Tento text je v češtině. Používám správnou diakritiku, háčky a čárky."


def _has_cuda():
    try:
        ctypes.cdll.LoadLibrary("cudart64_12.dll")
        return True
    except OSError:
        return False


class Transcriber:
    def __init__(self):
        if _has_cuda():
            self._model_size = "medium"
            self._device = "cuda"
            self._compute_type = "float16"
        else:
            self._model_size = "medium"
            self._device = "cpu"
            self._compute_type = "int8"

        print(f"Loading Whisper model '{self._model_size}' on {self._device}...")
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        print("Model loaded.")

    @property
    def model_size(self):
        return self._model_size

    @property
    def device(self):
        return self._device

    def transcribe(self, audio_path):
        segments, info = self._model.transcribe(
            audio_path,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,
            initial_prompt=INITIAL_PROMPT,
        )

        texts = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            if texts and text == texts[-1]:
                continue
            texts.append(text)

        try:
            os.remove(audio_path)
        except OSError:
            pass

        return " ".join(texts)
