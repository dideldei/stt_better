"""
Fake Background Service for Ticket 5.1.

Demonstrates thread-safe communication: Background thread generates fake events,
UI processes them in UI thread. No widget updates from threads.
"""

import threading
import time
from typing import Callable, Optional

from util.logging_setup import get_logger


logger = get_logger(__name__)


class FakeBackgroundService:
    """
    Fake background service that generates fake events.
    
    This service runs in a background thread and generates fake events
    that are sent to the UI thread for processing.
    
    Per AGENTS.md and UNIFIED.md:
    - Background threads only generate events
    - No widget updates from threads
    - Communication via Events/Queue/Messages
    """
    
    def __init__(self, event_callback: Callable[[str, int], None]) -> None:
        """
        Initialize fake background service.
        
        Args:
            event_callback: Function to call when an event is generated.
                           Signature: callback(message: str, thread_id: int)
                           Must be thread-safe and will be called from background thread.
        """
        self.event_callback = event_callback
        self.background_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.background_thread_id: Optional[int] = None
    
    def start(self) -> None:
        """Start the fake background service."""
        if self.is_running:
            logger.warning("FakeBackgroundService already running")
            return
        
        logger.info("Starting FakeBackgroundService")
        self.is_running = True
        self.background_thread = threading.Thread(
            target=self._background_worker,
            daemon=True,
            name="FakeBackgroundWorker"
        )
        self.background_thread.start()
        logger.info("FakeBackgroundService started")
    
    def stop(self) -> None:
        """Stop the fake background service."""
        if not self.is_running:
            return
        
        logger.info("Stopping FakeBackgroundService")
        self.is_running = False
        if self.background_thread:
            self.background_thread.join(timeout=2.0)
        logger.info("FakeBackgroundService stopped")
    
    def _background_worker(self) -> None:
        """
        Background worker thread that generates fake events.
        
        This runs in a separate thread and generates fake events
        that are sent to the UI thread via the callback.
        """
        self.background_thread_id = threading.get_native_id()
        logger.info(
            f"[Background-Thread {self.background_thread_id}] "
            "FakeBackgroundWorker started"
        )
        
        # Generate 10 fake events, one per second
        for i in range(10):
            if not self.is_running:
                break
            
            time.sleep(1.0)  # 1 event per second
            
            message = f"Fake event {i+1}/10"
            logger.info(
                f"[Background-Thread {self.background_thread_id}] "
                f"Generating fake event: {message}"
            )
            
            # Call callback to send event to UI thread
            # The callback must be thread-safe (e.g., uses call_from_thread)
            self.event_callback(message, self.background_thread_id)
        
        # Final event
        if self.is_running:
            final_message = "Fake background task completed"
            logger.info(
                f"[Background-Thread {self.background_thread_id}] "
                f"Generating final event: {final_message}"
            )
            self.event_callback(final_message, self.background_thread_id)
        
        logger.info(
            f"[Background-Thread {self.background_thread_id}] "
            "FakeBackgroundWorker finished"
        )
        self.is_running = False
