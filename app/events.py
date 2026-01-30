"""
Central event definitions (re-export from domain).

Per STRUCTURE.md section 4.2, events are defined centrally here.
This module re-exports all events from domain.events for convenience.
"""

# Re-export all events from domain
from domain.events import (
    AppEvent,
    DoctorCompleted,
    FullSTTDone,
    FullSTTFail,
    KeyF2Pressed,
    KeyF8Pressed,
    KeyF9Pressed,
    KeyF10Pressed,
    QuitRequested,
)

__all__ = [
    "AppEvent",
    "KeyF9Pressed",
    "KeyF10Pressed",
    "KeyF8Pressed",
    "KeyF2Pressed",
    "QuitRequested",
    "FullSTTDone",
    "FullSTTFail",
    "DoctorCompleted",
]
