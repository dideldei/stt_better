"""
Main entry point for STT-Diktat-Agent.

Loads configuration, sets up logging, and runs the Textual app.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from util.config_loader import load_config
from util.logging_setup import setup_logging, get_logger
from ui.fokus_tui import FokusTUI


def main() -> None:
    """Main entry point"""
    # Set up logging first (before config loading, so we can log config errors)
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting STT-Diktat-Agent")
    
    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except SystemExit:
        # Config loader already printed error and exited
        # Re-raise to ensure clean exit
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
    
    # Log config summary (no PHI)
    logger.info(f"Audio: {config.audio.samplerate}Hz, {config.audio.channels}ch")
    logger.info(f"Snippet: {config.snippet.seconds}s")
    logger.info(f"STT model: {config.stt.model}")
    
    # Create and run the Textual app
    try:
        app = FokusTUI()
        logger.info("Starting Textual app")
        app.run()
        logger.info("Textual app exited cleanly")
    except KeyboardInterrupt:
        logger.info("App interrupted by user")
    except Exception as e:
        logger.error(f"Error running app: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)
    
    logger.info("STT-Diktat-Agent shutdown complete")


if __name__ == "__main__":
    main()
