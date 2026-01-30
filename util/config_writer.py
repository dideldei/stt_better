"""
Configuration writer for STT-Diktat-Agent.

Provides functions to update config.toml programmatically.
Preserves existing config structure and comments where possible.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: tomllib (Python 3.11+) or tomli required for config reading")
        sys.exit(1)

try:
    import tomli_w
except ImportError:
    print("ERROR: tomli-w required for config writing. Install with: pip install tomli-w")
    sys.exit(1)

from util.logging_setup import get_logger


logger = get_logger(__name__)


def update_audio_device(config_path: Path, device: str) -> None:
    """
    Update the audio.device field in config.toml.
    
    Args:
        config_path: Path to config.toml file
        device: Device identifier to save (device name or empty string for default)
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        IOError: If file cannot be read or written
    """
    if not config_path.exists():
        error_msg = f"Config file not found: {config_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        # Read existing config
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
        
        # Update audio.device field
        if "audio" not in config_data:
            config_data["audio"] = {}
        
        old_device = config_data["audio"].get("device", "")
        config_data["audio"]["device"] = device
        
        # Write updated config back
        with open(config_path, "wb") as f:
            tomli_w.dump(config_data, f)
        
        logger.info(
            f"Updated audio device in config: '{old_device}' -> '{device}'"
        )
        
    except tomllib.TOMLDecodeError as e:
        error_msg = f"Failed to parse config.toml: {e}"
        logger.error(error_msg)
        raise IOError(error_msg) from e
    except IOError as e:
        error_msg = f"Failed to read/write config.toml: {e}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error updating config: {e}"
        logger.error(error_msg)
        raise IOError(error_msg) from e
