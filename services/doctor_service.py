"""
Doctor/Preflight service for STT-Diktat-Agent.

Performs system checks before starting the application:
- Path write tests
- Requirements check
- STT model loadability
- Microphone availability

Runs asynchronously and posts results via callback.
No PHI in logs or error messages.
"""

import threading
from pathlib import Path
from typing import Callable, Optional
import tempfile

from util.logging_setup import get_logger
from util.config_loader import load_config
from util.config_writer import update_audio_device
from services.audio_capture import check_microphone


logger = get_logger(__name__)


class DoctorCheckResult:
    """Result of a doctor check."""
    
    def __init__(
        self,
        success: bool,
        error_code: Optional[str] = None,
        error_hint: Optional[str] = None,
        mic_ok: bool = True,
        model_ok: bool = True,
    ) -> None:
        self.success = success
        self.error_code = error_code
        self.error_hint = error_hint
        self.mic_ok = mic_ok
        self.model_ok = model_ok


class DoctorService:
    """
    Doctor/Preflight service.
    
    Performs system checks and returns results via callback.
    Designed to run in background thread without blocking UI.
    """
    
    def __init__(self, project_root: Path) -> None:
        """
        Initialize doctor service.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.data_dir = project_root / "data"
    
    def run_checks(
        self,
        callback: Callable[[DoctorCheckResult], None]
    ) -> None:
        """
        Run all doctor checks asynchronously.
        
        Args:
            callback: Function to call with results (thread-safe, use call_from_thread)
        """
        def _run_in_thread() -> None:
            """Run checks in background thread."""
            thread_id = threading.get_native_id()
            logger.info(f"[Doctor-Thread {thread_id}] Starting doctor checks")
            
            result = self._perform_checks()
            
            logger.info(
                f"[Doctor-Thread {thread_id}] Doctor checks completed: "
                f"success={result.success}, mic_ok={result.mic_ok}, model_ok={result.model_ok}"
            )
            
            # Call callback with result
            callback(result)
        
        # Start background thread
        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
    
    def _perform_checks(self) -> DoctorCheckResult:
        """
        Perform all doctor checks.
        
        Returns:
            DoctorCheckResult with success/failure and error details
        """
        # Check 1: Path write tests
        path_check = self._check_paths()
        if not path_check[0]:
            return DoctorCheckResult(
                success=False,
                error_code="PATH_NOT_WRITABLE",
                error_hint=path_check[1],
                mic_ok=False,
                model_ok=False,
            )
        
        # Check 2: requirements.lock.txt exists
        req_check = self._check_requirements()
        if not req_check[0]:
            logger.warning(f"Requirements check: {req_check[1]}")
            # Continue - this is informational only per ticket spec
        
        # Check 3: STT model loadability
        model_check = self._check_stt_model()
        model_ok = model_check[0]
        if not model_ok:
            return DoctorCheckResult(
                success=False,
                error_code="MODEL_NOT_LOADABLE",
                error_hint=model_check[1],
                mic_ok=True,  # We haven't checked mic yet, assume OK
                model_ok=False,
            )
        
        # Check 4: Microphone availability
        mic_check = self._check_microphone()
        mic_ok = mic_check[0]
        mic_error_hint = mic_check[1]
        mic_device = mic_check[2]  # Device identifier (saved to config if successful)
        
        if not mic_ok:
            return DoctorCheckResult(
                success=False,
                error_code="MIC_NOT_AVAILABLE",
                error_hint=mic_error_hint,
                mic_ok=False,
                model_ok=True,
            )
        
        # All checks passed
        return DoctorCheckResult(
            success=True,
            mic_ok=True,
            model_ok=True,
        )
    
    def _check_paths(self) -> tuple[bool, Optional[str]]:
        """
        Check if all required data paths are writable.
        
        Returns:
            (success, error_hint)
        """
        required_dirs = [
            "recordings",
            "transcripts",
            "db",
            "logs",
            "cache",
        ]
        
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories if they don't exist
            for subdir in required_dirs:
                dir_path = self.data_dir / subdir
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Test write access with a temp file
                test_file = dir_path / ".doctor_test_write"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    logger.info(f"Path check OK: {dir_path}")
                except Exception as e:
                    error_hint = f"Cannot write to {dir_path.name}/ directory"
                    logger.error(f"Path check FAIL: {dir_path} - {e}")
                    return (False, error_hint)
            
            return (True, None)
            
        except Exception as e:
            error_hint = "Cannot create/access data directories"
            logger.error(f"Path check FAIL: {e}")
            return (False, error_hint)
    
    def _check_requirements(self) -> tuple[bool, Optional[str]]:
        """
        Check if requirements.lock.txt exists.
        
        This is informational only - we don't enforce it.
        
        Returns:
            (success, info_message)
        """
        req_file = self.project_root / "requirements.lock.txt"
        
        if req_file.exists():
            logger.info(f"Requirements check OK: {req_file}")
            return (True, None)
        else:
            info_msg = "requirements.lock.txt not found (informational)"
            logger.warning(info_msg)
            return (False, info_msg)
    
    def _check_stt_model(self) -> tuple[bool, Optional[str]]:
        """
        Check if STT model is loadable.
        
        We try to load the model without forcing download.
        If model isn't cached, we allow it to download once.
        
        Returns:
            (success, error_hint)
        """
        try:
            # Import here to avoid import errors if faster-whisper not installed
            from faster_whisper import WhisperModel
            
            # Read model name from config (default to "small")
            model_name = "small"
            try:
                from util.config_loader import load_config
                config = load_config()
                model_name = config.stt.model
            except Exception as e:
                logger.warning(f"Could not load config for model name, using default 'small': {e}")
            
            logger.info(f"STT model check: Loading model '{model_name}'...")
            
            # Try to load the model
            # This will download if not cached, which is acceptable per spec
            model = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                download_root=str(self.data_dir / "cache"),
            )
            
            logger.info(f"STT model check OK: Model '{model_name}' loaded successfully")
            
            # Clean up model to free memory
            del model
            
            return (True, None)
            
        except ImportError:
            error_hint = "faster-whisper not installed"
            logger.error(f"STT model check FAIL: {error_hint}")
            return (False, error_hint)
        except Exception as e:
            error_hint = f"Cannot load STT model: {type(e).__name__}"
            logger.error(f"STT model check FAIL: {e}")
            return (False, error_hint)
    
    def _check_microphone(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if microphone devices are available and working.
        
        Tests devices by actually opening streams to verify access.
        Saves working device to config.toml for next run.
        
        Returns:
            (success, error_hint, device_identifier)
        """
        try:
            # Load config to get current audio settings
            config = load_config()
            
            # Perform microphone check with stream testing
            success, error_hint, device_identifier = check_microphone(
                self.project_root,
                config
            )
            
            # If check succeeded and we have a device identifier, save it to config
            if success and device_identifier is not None:
                try:
                    config_path = self.project_root / "config.toml"
                    # Only update if device changed
                    if device_identifier != config.audio.device:
                        update_audio_device(config_path, device_identifier)
                        logger.info(f"Saved working device to config: '{device_identifier}'")
                except Exception as e:
                    # Don't fail the check if we can't save to config
                    logger.warning(f"Could not save device to config: {e}")
            
            return (success, error_hint, device_identifier)
            
        except Exception as e:
            error_hint = f"Microphone check error: {type(e).__name__}"
            logger.error(f"Microphone check FAIL: {e}")
            return (False, error_hint, None)
