"""
STT Service for STT-Diktat-Agent (Ticket 8.1).

Loads faster-whisper model at startup, performs warmup, and keeps model ready.
CPU-only operation per specification.

Follows threading rules:
- Model loading/warmup in background thread
- No widget updates from threads
- Communication via callbacks
"""

import threading
import numpy as np
from pathlib import Path
from typing import Any, Callable, Optional

from util.logging_setup import get_logger
from util.config_loader import AppConfig


logger = get_logger(__name__)


class STTServiceResult:
    """Result of STT service initialization."""
    
    def __init__(
        self,
        success: bool,
        error_hint: Optional[str] = None,
    ) -> None:
        self.success = success
        self.error_hint = error_hint


class SnippetTranscriptionResult:
    """Result of snippet transcription (Ticket 8.2)."""
    
    def __init__(
        self,
        success: bool,
        transcript: Optional[str] = None,
        quality: Optional[str] = None,
        error_hint: Optional[str] = None,
    ) -> None:
        self.success = success
        self.transcript = transcript
        self.quality = quality
        self.error_hint = error_hint


class FullTranscriptionResult:
    """Result of full transcription (Ticket 8.3)."""
    
    def __init__(
        self,
        success: bool,
        transcript: Optional[str] = None,
        error_code: Optional[str] = None,
        error_hint: Optional[str] = None,
        job_id: str = "",
    ) -> None:
        self.success = success
        self.transcript = transcript
        self.error_code = error_code
        self.error_hint = error_hint
        self.job_id = job_id


class STTService:
    """
    STT service using faster-whisper.
    
    Loads model at startup, performs warmup, and keeps model ready for use.
    Initialization runs in background thread to avoid blocking UI.
    
    Per UNIFIED.md 7.4:
    - Model load + warmup beim Start (Doctor)
    - CPU-only (device="cpu")
    - Uses config for model, compute_type, beam_size, language
    """
    
    def __init__(self, project_root: Path, config: AppConfig) -> None:
        """
        Initialize STT service.
        
        Args:
            project_root: Path to project root directory
            config: Application configuration with STT settings
        """
        self.project_root = project_root
        self.config = config
        self.data_dir = project_root / "data"
        self.cache_dir = self.data_dir / "cache"
        
        # Model instance (loaded in background thread)
        self.model: Optional[Any] = None
        self._is_ready = False
        self._initialization_thread: Optional[threading.Thread] = None
    
    def initialize(
        self,
        callback: Callable[[STTServiceResult], None]
    ) -> None:
        """
        Initialize STT service asynchronously.
        
        Loads model and performs warmup in background thread.
        
        Args:
            callback: Function to call with results (thread-safe, use call_from_thread)
        """
        def _run_in_thread() -> None:
            """Run initialization in background thread."""
            thread_id = threading.get_native_id()
            logger.info(f"[STT-Thread {thread_id}] Starting STT service initialization")
            
            result = self._load_and_warmup()
            
            logger.info(
                f"[STT-Thread {thread_id}] STT service initialization completed: "
                f"success={result.success}"
            )
            
            # Call callback with result
            callback(result)
        
        # Start background thread
        self._initialization_thread = threading.Thread(
            target=_run_in_thread,
            daemon=True,
            name="STTInitWorker"
        )
        self._initialization_thread.start()
    
    def _load_and_warmup(self) -> STTServiceResult:
        """
        Load model and perform warmup.
        
        This runs in background thread.
        
        Returns:
            STTServiceResult with success/failure and error details
        """
        thread_id = threading.get_native_id()
        
        try:
            # Import here to catch import errors
            from faster_whisper import WhisperModel
            
            # Log configuration
            logger.info(
                f"[STT-Thread {thread_id}] Loading model: {self.config.stt.model}, "
                f"device=cpu, compute_type={self.config.stt.compute_type}"
            )
            
            # Load model with CPU-only settings (per ticket 8.1)
            self.model = WhisperModel(
                self.config.stt.model,
                device="cpu",  # CPU-only per ticket
                compute_type=self.config.stt.compute_type,
                download_root=str(self.cache_dir),
            )
            
            logger.info(
                f"[STT-Thread {thread_id}] Model loaded successfully: {self.config.stt.model}"
            )
            
            # Perform warmup
            logger.info(f"[STT-Thread {thread_id}] Starting warmup...")
            self._warmup()
            logger.info(f"[STT-Thread {thread_id}] Warmup completed successfully")
            
            self._is_ready = True
            return STTServiceResult(success=True)
            
        except ImportError as e:
            error_hint = "faster-whisper not installed"
            logger.error(f"[STT-Thread {thread_id}] STT service init FAIL: {error_hint}")
            return STTServiceResult(success=False, error_hint=error_hint)
        except Exception as e:
            error_hint = f"Cannot load STT model: {type(e).__name__}"
            logger.error(f"[STT-Thread {thread_id}] STT service init FAIL: {e}")
            return STTServiceResult(success=False, error_hint=error_hint)
    
    def _warmup(self) -> None:
        """
        Perform warmup by transcribing silence.
        
        This initializes the model's internal state and caches.
        Runs in background thread.
        """
        thread_id = threading.get_native_id()
        
        # Generate 1 second of silence (16kHz mono, per config.toml)
        # faster-whisper expects float32 numpy array
        silence = np.zeros(16000, dtype=np.float32)
        
        logger.info(
            f"[STT-Thread {thread_id}] Running warmup transcription on 1s silence"
        )
        
        # Transcribe silence to initialize model
        # Use configured language and beam_size
        segments, info = self.model.transcribe(
            silence,
            language=self.config.stt.language,
            beam_size=self.config.stt.beam_size,
            initial_prompt=self.config.stt.initial_prompt,
        )
        
        # Consume segments iterator (even though it's likely empty)
        _ = list(segments)
        
        logger.info(
            f"[STT-Thread {thread_id}] Warmup transcription complete "
            f"(language={info.language}, duration={info.duration:.2f}s)"
        )
    
    def is_ready(self) -> bool:
        """
        Check if STT service is ready.
        
        Returns:
            True if model is loaded and warmed up, False otherwise
        """
        return self._is_ready
    
    def get_model(self):
        """
        Get the loaded model instance.
        
        Returns:
            WhisperModel instance, or None if not loaded yet
        
        Note:
            Model is read-only after loading. Thread-safe for reading.
            Future tickets (8.2, 8.3) will use this for transcription.
        """
        return self.model
    
    def transcribe_snippet(
        self,
        audio_data: np.ndarray,
        callback: Callable[[SnippetTranscriptionResult], None]
    ) -> None:
        """
        Transcribe audio snippet asynchronously (Ticket 8.2).
        
        Runs transcription in background thread to avoid blocking UI.
        Calculates quality from faster-whisper metrics.
        
        Args:
            audio_data: Audio data as numpy array (float32, 16kHz mono)
            callback: Function to call with result (thread-safe, use call_from_thread)
        """
        def _run_transcription() -> None:
            """Run transcription in background thread."""
            thread_id = threading.get_native_id()
            logger.info(
                f"[STT-Thread {thread_id}] Starting snippet transcription "
                f"(audio length: {len(audio_data) / 16000:.1f}s)"
            )
            
            result = self._transcribe_snippet_internal(audio_data)
            
            logger.info(
                f"[STT-Thread {thread_id}] Snippet transcription completed: "
                f"success={result.success}"
            )
            
            # Call callback with result
            callback(result)
        
        # Start background thread
        transcription_thread = threading.Thread(
            target=_run_transcription,
            daemon=True,
            name="SnippetSTTWorker"
        )
        transcription_thread.start()
    
    def transcribe_full(
        self,
        audio_data: np.ndarray,
        job_id: str,
        callback: Callable[[FullTranscriptionResult], None],
    ) -> None:
        """
        Transcribe full audio asynchronously (Ticket 8.3).
        
        Runs in a single daemon thread (FullSTTWorker). Exactly one worker per
        PROCESSING; callback is invoked from that thread (use call_from_thread).
        
        Args:
            audio_data: Audio as numpy array (float32, 16kHz mono)
            job_id: Job identifier for the transcription
            callback: Called with FullTranscriptionResult (thread-safe)
        """
        def _run_full_transcription() -> None:
            thread_id = threading.get_native_id()
            logger.info(
                f"[STT-Thread {thread_id}] Starting full transcription "
                f"(job_id={job_id}, audio: {len(audio_data) / 16000:.1f}s)"
            )
            result = self._transcribe_full_internal(audio_data, job_id)
            logger.info(
                f"[STT-Thread {thread_id}] Full transcription completed: "
                f"success={result.success}"
            )
            callback(result)
        
        if not self._is_ready or self.model is None:
            fail = FullTranscriptionResult(
                success=False,
                error_code="STT_NOT_READY",
                error_hint="STT nicht bereit",
                job_id=job_id,
            )
            t = threading.Thread(
                target=lambda: callback(fail),
                daemon=True,
                name="FullSTTWorker",
            )
            t.start()
            return
        
        t = threading.Thread(
            target=_run_full_transcription,
            daemon=True,
            name="FullSTTWorker",
        )
        t.start()
    
    def _transcribe_full_internal(
        self,
        audio_data: np.ndarray,
        job_id: str,
    ) -> FullTranscriptionResult:
        """
        Perform full transcription (internal, runs in FullSTTWorker thread).
        
        Args:
            audio_data: Audio as numpy array (float32, 16kHz mono)
            job_id: Job identifier
        
        Returns:
            FullTranscriptionResult with transcript or error_code/error_hint
        """
        thread_id = threading.get_native_id()
        
        if not self._is_ready or self.model is None:
            return FullTranscriptionResult(
                success=False,
                error_code="STT_NOT_READY",
                error_hint="STT nicht bereit",
                job_id=job_id,
            )
        
        try:
            if audio_data is None or len(audio_data) == 0:
                return FullTranscriptionResult(
                    success=False,
                    error_code="AUDIO_INVALID",
                    error_hint="Audio-Daten ungültig",
                    job_id=job_id,
                )
            
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            segments, info = self.model.transcribe(
                audio_data,
                language=self.config.stt.language,
                beam_size=self.config.stt.beam_size,
                initial_prompt=self.config.stt.initial_prompt,
            )
            segments_list = list(segments)
            transcript_text = " ".join(s.text for s in segments_list).strip()
            logger.info(
                f"[STT-Thread {thread_id}] Full transcription: "
                f"language={info.language}, duration={info.duration:.2f}s, "
                f"segments={len(segments_list)}"
            )
            
            return FullTranscriptionResult(
                success=True,
                transcript=transcript_text,
                job_id=job_id,
            )
        except Exception as e:
            logger.error(
                f"[STT-Thread {thread_id}] Full STT FAIL: {e}",
                exc_info=True,
            )
            return FullTranscriptionResult(
                success=False,
                error_code=type(e).__name__,
                error_hint=str(e),
                job_id=job_id,
            )
    
    def _transcribe_snippet_internal(
        self,
        audio_data: np.ndarray
    ) -> SnippetTranscriptionResult:
        """
        Perform snippet transcription (internal, runs in background thread).
        
        Args:
            audio_data: Audio data as numpy array (float32, 16kHz mono)
        
        Returns:
            SnippetTranscriptionResult with transcript, quality, or error
        """
        thread_id = threading.get_native_id()
        
        # Check if service is ready
        if not self._is_ready or self.model is None:
            error_hint = "STT nicht bereit"
            logger.error(f"[STT-Thread {thread_id}] Snippet STT FAIL: {error_hint}")
            return SnippetTranscriptionResult(
                success=False,
                error_hint=error_hint
            )
        
        try:
            # Validate audio data
            if audio_data is None or len(audio_data) == 0:
                error_hint = "Audio-Daten ungültig"
                logger.error(f"[STT-Thread {thread_id}] Snippet STT FAIL: {error_hint}")
                return SnippetTranscriptionResult(
                    success=False,
                    error_hint=error_hint
                )
            
            # Ensure audio data is float32
            if audio_data.dtype != np.float32:
                logger.warning(
                    f"[STT-Thread {thread_id}] Converting audio from {audio_data.dtype} to float32"
                )
                audio_data = audio_data.astype(np.float32)
            
            # Transcribe audio
            logger.info(f"[STT-Thread {thread_id}] Calling model.transcribe()...")
            segments, info = self.model.transcribe(
                audio_data,
                language=self.config.stt.language,
                beam_size=self.config.stt.beam_size,
                initial_prompt=self.config.stt.initial_prompt,
            )

            # Extract text from segments
            segments_list = list(segments)
            transcript_text = " ".join(segment.text for segment in segments_list).strip()
            
            # Log transcription info (no PHI - only metadata)
            logger.info(
                f"[STT-Thread {thread_id}] Transcription complete: "
                f"language={info.language}, duration={info.duration:.2f}s, "
                f"segments={len(segments_list)}"
            )
            
            # Calculate quality from metrics
            quality = self._calculate_quality(
                no_speech_prob=info.language_probability if hasattr(info, 'language_probability') else 0.0,
                segments=segments_list
            )
            logger.info(
                f"[STT-Thread {thread_id}] Quality assessment: {quality}"
            )
            
            return SnippetTranscriptionResult(
                success=True,
                transcript=transcript_text,
                quality=quality
            )
            
        except Exception as e:
            error_hint = f"STT-Fehler: {type(e).__name__}"
            logger.error(
                f"[STT-Thread {thread_id}] Snippet STT FAIL: {e}",
                exc_info=True
            )
            return SnippetTranscriptionResult(
                success=False,
                error_hint=error_hint
            )
    
    def _calculate_quality(
        self,
        no_speech_prob: float,
        segments: list
    ) -> str:
        """
        Calculate quality indicator from STT metrics (Ticket 8.2).
        
        Per UNIFIED.md 7.5: Uses faster-whisper metrics to determine quality.
        
        Args:
            no_speech_prob: Probability of no speech (lower is better)
            segments: List of transcription segments with metrics
        
        Returns:
            Quality string with emoji and recommendation
            Format: "🟢/🟡/🔴 Qualität: <description>"
        """
        # If no segments, quality is poor
        if not segments:
            return "🔴 Qualität: Keine Sprache erkannt"
        
        # Calculate average metrics from segments
        avg_logprob_sum = 0.0
        compression_ratio_sum = 0.0
        no_speech_prob_sum = 0.0
        count = 0
        
        for segment in segments:
            if hasattr(segment, 'avg_logprob'):
                avg_logprob_sum += segment.avg_logprob
                count += 1
            if hasattr(segment, 'compression_ratio'):
                compression_ratio_sum += segment.compression_ratio
            if hasattr(segment, 'no_speech_prob'):
                no_speech_prob_sum += segment.no_speech_prob
        
        if count == 0:
            # No metrics available, return neutral quality
            return "🟡 Qualität: Unbekannt"
        
        avg_logprob = avg_logprob_sum / count
        avg_compression_ratio = compression_ratio_sum / count
        avg_no_speech_prob = no_speech_prob_sum / count
        
        # Quality thresholds based on faster-whisper typical values
        # avg_logprob: typically ranges from -1.0 (good) to -3.0 (poor)
        # no_speech_prob: < 0.3 is good, > 0.6 is poor
        # compression_ratio: 1.5-3.0 is normal, > 3.5 or < 1.2 is suspicious
        
        # Check for poor quality conditions
        if avg_no_speech_prob > 0.6:
            return "🔴 Qualität: Möglicherweise keine Sprache"
        
        if avg_logprob < -2.5:
            return "🔴 Qualität: Niedrig (undeutlich)"
        
        if avg_compression_ratio > 3.5:
            return "🔴 Qualität: Niedrig (zu repetitiv)"
        
        if avg_compression_ratio < 1.2:
            return "🔴 Qualität: Niedrig (zu wenig Inhalt)"
        
        # Check for medium quality conditions
        if avg_no_speech_prob > 0.3:
            return "🟡 Qualität: Mittel (unsicher)"
        
        if avg_logprob < -1.5:
            return "🟡 Qualität: Mittel"
        
        if avg_compression_ratio > 3.0 or avg_compression_ratio < 1.5:
            return "🟡 Qualität: Mittel (ungewöhnlich)"
        
        # Good quality
        return "🟢 Qualität: Gut"
