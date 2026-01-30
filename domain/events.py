"""
Event definitions for the STT-Diktat-Agent.

Events are used for communication between UI and services.
All events are dataclasses for type safety and clarity.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AppEvent:
    """
    Base class for all application events.
    
    All events are immutable (frozen) to prevent accidental modification.
    """
    pass


# UI Events (triggered by user input)


@dataclass(frozen=True)
class KeyF9Pressed(AppEvent):
    """F9 key pressed - Record/Pause/Resume or start new dictation."""
    pass


@dataclass(frozen=True)
class KeyF10Pressed(AppEvent):
    """F10 key pressed - Stop recording and start Full-STT."""
    pass


@dataclass(frozen=True)
class KeyF8Pressed(AppEvent):
    """F8 key pressed - Redo with better model."""
    pass


@dataclass(frozen=True)
class KeyF2Pressed(AppEvent):
    """F2 key pressed - Doctor/Preflight check."""
    pass


@dataclass(frozen=True)
class QuitRequested(AppEvent):
    """Esc key pressed - Quit request (may require confirmation)."""
    pass


# Service Events (triggered by services/background tasks)


@dataclass(frozen=True)
class FullSTTDone(AppEvent):
    """Full STT processing completed successfully."""
    transcript: str
    job_id: str


@dataclass(frozen=True)
class FullSTTFail(AppEvent):
    """Full STT processing failed."""
    error_code: str
    error_hint: str
    job_id: str


@dataclass(frozen=True)
class DoctorCompleted(AppEvent):
    """Doctor/Preflight check completed."""
    success: bool
    error_code: Optional[str] = None
    error_hint: Optional[str] = None


@dataclass(frozen=True)
class AudioLevelUpdated(AppEvent):
    """Audio level updated from fake audio service (Ticket 6.1)."""
    level: float  # 0.0 to 1.0
    thread_id: int  # For logging thread separation
