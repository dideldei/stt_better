"""
App State definitions.

Defines all valid UI states for the STT-Diktat-Agent.
States are UI-focused and represent the current application mode.
"""

from enum import Enum


class AppState(str, Enum):
    """
    Application states (UI-focused).
    
    States:
    - INIT: Initial state during startup/Doctor preflight
    - READY: Ready to start recording
    - RECORDING: Currently recording audio
    - PAUSED: Recording paused
    - PROCESSING: Processing audio with STT
    - DONE: Transcription complete
    - ERROR: Error state
    """
    
    INIT = "INIT"
    READY = "READY"
    RECORDING = "RECORDING"
    PAUSED = "PAUSED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"
    
    def __str__(self) -> str:
        """String representation for logging."""
        return self.value
