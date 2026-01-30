"""
Snippet Tracker Service for Ticket 7.1 & 8.2.

Tracks cumulative recording time and triggers snippet STT after configured threshold.
Background thread only counts time when recording (not when paused).

Ticket 8.2: Uses real STT transcription instead of fake snippets.
"""

import numpy as np
import threading
import time
from typing import Callable, Optional, TYPE_CHECKING

from util.logging_setup import get_logger

if TYPE_CHECKING:
    from services.stt_service import STTService

logger = get_logger(__name__)


class SnippetTrackerService:
    """
    Snippet tracker service that monitors cumulative recording time.
    
    This service runs in a background thread and tracks how long recording
    has been active (pauses don't count). When the configured threshold is
    reached, it triggers real STT transcription (Ticket 8.2).
    
    Per AGENTS.md and UNIFIED.md:
    - Background threads only generate events
    - No widget updates from threads
    - Communication via Events/Queue/Messages
    """
    
    def __init__(
        self,
        snippet_callback: Callable[[str, str, int, Optional[str]], None],
        stt_service: Optional['STTService'],
        threshold_seconds: float = 8.0,
        get_audio_for_snippet: Optional[Callable[[], Optional[np.ndarray]]] = None,
    ) -> None:
        """
        Initialize snippet tracker service (Ticket 8.2).
        
        Args:
            snippet_callback: Function to call when snippet is ready.
            stt_service: STT service for real transcription (Ticket 8.2)
            threshold_seconds: Time in seconds before snippet is triggered (default 8.0)
            get_audio_for_snippet: If set, called to get real mic audio for snippet; else use fake.
        """
        self.snippet_callback = snippet_callback
        self.stt_service = stt_service
        self.threshold_seconds = threshold_seconds
        self.get_audio_for_snippet = get_audio_for_snippet
        self.background_thread: Optional[threading.Thread] = None
        self.background_thread_id: Optional[int] = None
        
        # State management
        self.is_running = False
        self.is_paused = False
        self.cumulative_time = 0.0
        self.snippet_triggered = False
        
        # Thread synchronization
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def start(self) -> None:
        """Start tracking cumulative recording time."""
        with self._lock:
            if self.is_running:
                logger.warning("SnippetTrackerService already running")
                return
            
            # Reset state for new recording session
            self.is_running = True
            self.is_paused = False
            self.cumulative_time = 0.0
            self.snippet_triggered = False
            self._stop_event.clear()
            
            logger.info(
                f"Starting SnippetTrackerService (threshold: {self.threshold_seconds}s)"
            )
            
            self.background_thread = threading.Thread(
                target=self._background_worker,
                daemon=True,
                name="SnippetTrackerWorker"
            )
            self.background_thread.start()
            logger.info("SnippetTrackerService started")
    
    def pause(self) -> None:
        """Pause time tracking (cumulative time is preserved)."""
        with self._lock:
            if not self.is_running:
                logger.warning("Cannot pause: SnippetTrackerService not running")
                return
            
            if self.is_paused:
                logger.warning("SnippetTrackerService already paused")
                return
            
            self.is_paused = True
            logger.info(
                f"SnippetTrackerService paused at {self.cumulative_time:.1f}s"
            )
    
    def resume(self) -> None:
        """Resume time tracking from where it was paused."""
        with self._lock:
            if not self.is_running:
                logger.warning("Cannot resume: SnippetTrackerService not running")
                return
            
            if not self.is_paused:
                logger.warning("SnippetTrackerService not paused")
                return
            
            self.is_paused = False
            logger.info(
                f"SnippetTrackerService resumed from {self.cumulative_time:.1f}s"
            )
    
    def stop(self) -> None:
        """Stop tracking and reset state."""
        with self._lock:
            if not self.is_running:
                return
            
            logger.info("Stopping SnippetTrackerService")
            self.is_running = False
            self._stop_event.set()
        
        # Wait for thread to finish (outside lock to avoid deadlock)
        if self.background_thread:
            self.background_thread.join(timeout=2.0)
        
        with self._lock:
            self.is_paused = False
            self.cumulative_time = 0.0
            self.snippet_triggered = False
            logger.info("SnippetTrackerService stopped")
    
    def _background_worker(self) -> None:
        """
        Background worker thread that tracks cumulative recording time.
        
        Checks time every 100ms and accumulates when not paused.
        When threshold is reached, triggers real STT transcription (Ticket 8.2).
        """
        self.background_thread_id = threading.get_native_id()
        logger.info(
            f"[Background-Thread {self.background_thread_id}] "
            "SnippetTrackerWorker started"
        )
        
        check_interval = 0.1  # Check every 100ms
        
        while not self._stop_event.is_set():
            time.sleep(check_interval)
            
            # Check state under lock
            with self._lock:
                if not self.is_running:
                    break
                
                # Only accumulate time if not paused and snippet not yet triggered
                if not self.is_paused and not self.snippet_triggered:
                    self.cumulative_time += check_interval
                    
                    # Check if threshold reached
                    if self.cumulative_time >= self.threshold_seconds:
                        self.snippet_triggered = True
                        logger.info(
                            f"[Background-Thread {self.background_thread_id}] "
                            f"Snippet threshold reached: {self.cumulative_time:.1f}s"
                        )
                        
                        # Trigger real STT transcription (Ticket 8.2)
                        self._transcribe_snippet()
        
        logger.info(
            f"[Background-Thread {self.background_thread_id}] "
            "SnippetTrackerWorker finished"
        )
    
    def _transcribe_snippet(self) -> None:
        """
        Trigger real STT transcription for snippet (Ticket 8.2).
        
        Generates fake audio data (until real audio capture is available),
        then calls STT service asynchronously. Result is sent to UI via callback.
        """
        # Check if STT service is available and ready
        if self.stt_service is None or not self.stt_service.is_ready():
            error_hint = "STT nicht bereit"
            logger.error(
                f"[Background-Thread {self.background_thread_id}] "
                f"Cannot transcribe snippet: {error_hint}"
            )
            # Send error to UI
            self.snippet_callback(
                "",  # empty transcript
                "🔴 Qualität: Fehler",
                self.background_thread_id,
                error_hint
            )
            return
        
        # Real mic audio if available, else fake
        raw: Optional[np.ndarray] = None
        if self.get_audio_for_snippet:
            try:
                raw = self.get_audio_for_snippet()
            except Exception as e:
                logger.debug("get_audio_for_snippet: %s", e)
        if raw is not None and len(raw) > 0:
            audio_data = raw.astype(np.float32, copy=False) if raw.dtype != np.float32 else raw
            uses_fake = False
        else:
            audio_length = int(self.threshold_seconds * 16000)
            audio_data = self._generate_fake_audio(audio_length)
            uses_fake = True
        logger.info(
            f"[Background-Thread {self.background_thread_id}] "
            f"Starting STT transcription (audio: {len(audio_data)} samples, real_mic={not uses_fake})"
        )
        
        # Define callback for STT result
        def handle_stt_result(result) -> None:
            """Handle STT transcription result (called from STT thread)."""
            if result.success:
                logger.info(
                    f"[Background-Thread {self.background_thread_id}] "
                    f"STT transcription successful: quality={result.quality}"
                )
                # Send transcript to UI
                self.snippet_callback(
                    result.transcript,
                    result.quality,
                    self.background_thread_id,
                    None  # no error
                )
            else:
                logger.error(
                    f"[Background-Thread {self.background_thread_id}] "
                    f"STT transcription failed: {result.error_hint}"
                )
                # Send error to UI
                self.snippet_callback(
                    "",  # empty transcript
                    "🔴 Qualität: Fehler",
                    self.background_thread_id,
                    result.error_hint
                )
        
        # Call STT service asynchronously
        self.stt_service.transcribe_snippet(audio_data, handle_stt_result)
    
    def _generate_fake_audio(self, length: int) -> np.ndarray:
        """
        Generate fake audio data (Ticket 8.2 temporary solution).
        
        This is a placeholder until real audio capture is implemented.
        Generates synthetic audio with some noise to simulate speech.
        
        Args:
            length: Number of samples (16000 samples = 1 second @ 16kHz)
        
        Returns:
            numpy array of float32 audio samples
        """
        # Generate white noise at low amplitude
        # This simulates some audio content for STT testing
        audio = np.random.normal(0, 0.1, length).astype(np.float32)
        
        # Add some structure to make it more speech-like
        # Simple envelope to simulate speech patterns
        envelope = np.sin(np.linspace(0, 10 * np.pi, length)) * 0.5 + 0.5
        audio = audio * envelope.astype(np.float32)
        
        logger.info(
            f"Generated fake audio: {length} samples ({length / 16000:.1f}s)"
        )
        
        return audio
