"""
Recording service for STT-Diktat-Agent.

Captures microphone audio during RECORDING/PAUSED into a buffer.
Provides get_snippet(seconds) and get_full() for Snippet-STT and Full-STT.
Uses sounddevice InputStream; falls back to empty buffer if unavailable.

Optional level_callback(level: float) is invoked at ≤10 Hz with a log-like
level (0..1) from the audio stream for a real level meter. Uses log(1 + k*rms)
to better match perceptual loudness (dB-like).
"""

import math
import threading
import time as _time
import numpy as np
from typing import Callable, Optional

from util.config_loader import AppConfig
from util.logging_setup import get_logger
from services.audio_capture import get_device_index

logger = get_logger(__name__)


class RecordingService:
    """
    Records from the microphone into a float32 16kHz mono buffer.
    start() / stop() / pause() / resume(). get_snippet(seconds) and get_full().
    If level_callback is set, calls it at ≤10 Hz with log-like level 0..1.
    """

    def __init__(
        self,
        config: AppConfig,
        level_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.config = config
        self._level_callback = level_callback
        self._last_level_time = 0.0
        self._stream: Optional[object] = None
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._samplerate = config.audio.samplerate
        self._channels = config.audio.channels
        self._device: Optional[int] = None

    def start(self) -> None:
        self._device = get_device_index(self.config)
        with self._lock:
            self._chunks = []
        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                device=self._device,
                channels=self._channels,
                samplerate=self._samplerate,
                dtype=np.float32,
                blocksize=1024,
                callback=self._callback,
            )
            self._stream.start()
            logger.info("RecordingService started (device=%s)", self._device)
        except Exception as e:
            logger.warning("RecordingService failed to start: %s", e)
            self._stream = None

    def _callback(self, indata: np.ndarray, frames: int, time: object, status: object) -> None:
        if status:
            logger.debug("RecordingService callback status: %s", status)
        with self._lock:
            self._chunks.append(indata.copy().flatten())
        if self._level_callback is not None:
            now = _time.monotonic()
            if now - self._last_level_time >= 0.1:
                arr = indata.flatten()
                rms = float(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))
                # Log-like mapping: more resolution at low levels, matches perceptual loudness
                _rms_max = 0.5
                _k = 20.0
                rms_capped = min(rms, _rms_max)
                raw = math.log(1.0 + _k * rms_capped)
                display = min(1.0, raw / math.log(1.0 + _k * _rms_max))
                self._last_level_time = now
                try:
                    self._level_callback(display)
                except Exception as e:
                    logger.debug("RecordingService level_callback: %s", e)

    def stop(self) -> None:
        if self._stream is None:
            return
        try:
            import sounddevice as sd
            if hasattr(self._stream, "stop"):
                self._stream.stop()
            if hasattr(self._stream, "close"):
                self._stream.close()
        except Exception as e:
            logger.debug("RecordingService stop: %s", e)
        self._stream = None
        logger.info("RecordingService stopped")

    def pause(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop()
        except Exception as e:
            logger.debug("RecordingService pause: %s", e)
        logger.info("RecordingService paused")

    def resume(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.start()
        except Exception as e:
            logger.warning("RecordingService resume: %s", e)
        logger.info("RecordingService resumed")

    def get_snippet(self, seconds: float) -> np.ndarray:
        """Last `seconds` of recorded audio, float32. Empty if none."""
        with self._lock:
            if not self._chunks:
                return np.array([], dtype=np.float32)
            buf = np.concatenate(self._chunks)
        n = int(seconds * self._samplerate)
        if len(buf) <= n:
            return buf
        return buf[-n:].astype(np.float32, copy=False)

    def get_full(self) -> np.ndarray:
        """Full buffer, float32. Empty if none."""
        with self._lock:
            if not self._chunks:
                return np.array([], dtype=np.float32)
            return np.concatenate(self._chunks).astype(np.float32, copy=False)
