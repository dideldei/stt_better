"""
State Machine for STT-Diktat-Agent.

Manages state transitions and validates allowed transitions.
All state changes are logged.
"""

from typing import Optional

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
from domain.states import AppState
from util.logging_setup import get_logger


logger = get_logger(__name__)


class StateMachine:
    """
    Central state machine for the application.
    
    Validates state transitions and logs all state changes.
    Blocks invalid transitions by returning None.
    """
    
    def __init__(self, initial_state: AppState = AppState.INIT) -> None:
        """
        Initialize state machine.
        
        Args:
            initial_state: Starting state (default: INIT)
        """
        self._current_state = initial_state
        logger.info(f"StateMachine initialized with state: {self._current_state}")
    
    @property
    def current_state(self) -> AppState:
        """Get current state."""
        return self._current_state
    
    def transition(self, event: AppEvent) -> Optional[AppState]:
        """
        Attempt state transition based on event.
        
        Args:
            event: The event triggering the transition
            
        Returns:
            New state if transition is valid, None if invalid
        """
        new_state = self._calculate_transition(self._current_state, event)
        
        if new_state is None:
            logger.warning(
                f"Invalid transition blocked: {self._current_state} --{type(event).__name__}--> (blocked)"
            )
            return None
        
        old_state = self._current_state
        self._current_state = new_state
        logger.info(f"State transition: {old_state} --{type(event).__name__}--> {new_state}")
        return new_state
    
    def _calculate_transition(self, from_state: AppState, event: AppEvent) -> Optional[AppState]:
        """
        Calculate new state based on current state and event.
        
        Returns None for invalid transitions.
        
        Transition rules (from UNIFIED.md section 5.3):
        - READY --F9--> RECORDING
        - RECORDING --F9--> PAUSED
        - PAUSED --F9--> RECORDING
        - RECORDING/PAUSED --F10--> PROCESSING
        - PROCESSING --FullSTT_Done--> DONE
        - PROCESSING --FullSTT_Fail--> ERROR
        - DONE --F8--> PROCESSING (Redo)
        - DONE --F9--> RECORDING (Start new dictation)
        - READY/DONE/ERROR --F2--> INIT (Doctor) -> READY/ERROR
        """
        # F9 transitions
        if isinstance(event, KeyF9Pressed):
            if from_state == AppState.READY:
                return AppState.RECORDING
            elif from_state == AppState.RECORDING:
                return AppState.PAUSED
            elif from_state == AppState.PAUSED:
                return AppState.RECORDING
            elif from_state == AppState.DONE:
                return AppState.RECORDING
            # Invalid: F9 in INIT, PROCESSING, ERROR
            return None
        
        # F10 transitions
        if isinstance(event, KeyF10Pressed):
            if from_state == AppState.RECORDING:
                return AppState.PROCESSING
            elif from_state == AppState.PAUSED:
                return AppState.PROCESSING
            # Invalid: F10 in other states
            return None
        
        # F8 transitions
        if isinstance(event, KeyF8Pressed):
            if from_state == AppState.DONE:
                return AppState.PROCESSING
            # Invalid: F8 in other states
            return None
        
        # F2 transitions (Doctor)
        if isinstance(event, KeyF2Pressed):
            if from_state in (AppState.READY, AppState.DONE, AppState.ERROR):
                return AppState.INIT
            # Invalid: F2 in RECORDING, PAUSED, PROCESSING
            return None
        
        # Doctor completed transitions
        if isinstance(event, DoctorCompleted):
            if from_state == AppState.INIT:
                if event.success:
                    return AppState.READY
                else:
                    return AppState.ERROR
            # Invalid: DoctorCompleted in other states
            return None
        
        # Full STT done transitions
        if isinstance(event, FullSTTDone):
            if from_state == AppState.PROCESSING:
                return AppState.DONE
            # Invalid: FullSTTDone in other states
            return None
        
        # Full STT fail transitions
        if isinstance(event, FullSTTFail):
            if from_state == AppState.PROCESSING:
                return AppState.ERROR
            # Invalid: FullSTTFail in other states
            return None
        
        # Unknown event type
        logger.warning(f"Unknown event type: {type(event).__name__}")
        return None
    
    def get_allowed_transitions(self, state: Optional[AppState] = None) -> list[type[AppEvent]]:
        """
        Get list of event types allowed in the given state.
        
        Args:
            state: State to check (default: current state)
            
        Returns:
            List of allowed event classes
        """
        if state is None:
            state = self._current_state
        
        allowed: list[type[AppEvent]] = []
        
        if state == AppState.INIT:
            # Only DoctorCompleted is allowed
            allowed.append(DoctorCompleted)
        elif state == AppState.READY:
            allowed.extend([KeyF9Pressed, KeyF2Pressed, QuitRequested])
        elif state == AppState.RECORDING:
            allowed.extend([KeyF9Pressed, KeyF10Pressed, QuitRequested])
        elif state == AppState.PAUSED:
            allowed.extend([KeyF9Pressed, KeyF10Pressed, QuitRequested])
        elif state == AppState.PROCESSING:
            allowed.extend([FullSTTDone, FullSTTFail, QuitRequested])
        elif state == AppState.DONE:
            allowed.extend([KeyF9Pressed, KeyF8Pressed, KeyF2Pressed, QuitRequested])
        elif state == AppState.ERROR:
            allowed.extend([KeyF2Pressed, QuitRequested])
        
        return allowed
