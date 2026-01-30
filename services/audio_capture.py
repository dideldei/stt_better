"""
Audio capture utilities for STT-Diktat-Agent.

Provides microphone device detection and testing functionality.
Tests devices by actually opening audio streams to verify access.
"""

import time
from pathlib import Path
from typing import Optional

from util.config_loader import AppConfig
from util.logging_setup import get_logger


logger = get_logger(__name__)


def check_microphone(
    project_root: Path,
    config: AppConfig
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Check if microphone devices are available and working.
    
    Tests devices by actually opening an InputStream to verify access.
    If a device from config works, it's returned. Otherwise, tries default
    device, then iterates through all input devices.
    
    Args:
        project_root: Path to project root directory
        config: Application configuration with audio settings
    
    Returns:
        Tuple of (success, error_hint, device_identifier)
        - success: True if a working device was found
        - error_hint: Error message if failed (None if success)
        - device_identifier: Device name to save to config (None = use default)
    """
    try:
        # Import here to avoid import errors if sounddevice not installed
        import sounddevice as sd
        
    except ImportError:
        error_hint = "sounddevice not installed"
        logger.error(f"Microphone check FAIL: {error_hint}")
        return (False, error_hint, None)
    
    # Get audio parameters from config
    samplerate = config.audio.samplerate
    channels = config.audio.channels
    device_preference = config.audio.device  # Empty string or device name
    
    try:
        # Query all devices
        devices = sd.query_devices()
        
        if not devices:
            error_hint = "No audio devices found"
            logger.error("Microphone check FAIL: No devices")
            return (False, error_hint, None)
        
        # Find input devices
        input_devices = [
            (idx, d) for idx, d in enumerate(devices)
            if isinstance(d, dict) and d.get('max_input_channels', 0) > 0
        ]
        
        if not input_devices:
            error_hint = "No input devices (microphones) found"
            logger.error("Microphone check FAIL: No input devices")
            return (False, error_hint, None)
        
        logger.info(f"Found {len(input_devices)} input device(s)")
        for idx, device in input_devices:
            name = device.get('name', 'Unknown')
            logger.info(f"  Device {idx}: {name}")
        
    except Exception as e:
        error_hint = f"Cannot query audio devices: {type(e).__name__}"
        logger.error(f"Microphone check FAIL: {e}")
        return (False, error_hint, None)
    
    # Build list of devices to test in priority order
    devices_to_test = []
    
    # 1. If config has device preference, try that first
    if device_preference:
        # Find device by name substring match
        for idx, device in input_devices:
            name = device.get('name', '')
            if device_preference.lower() in name.lower():
                devices_to_test.append((idx, device, f"config preference '{device_preference}'"))
                logger.info(f"Testing config device first: {name} (index {idx})")
                break
    
    # 2. Try default device (None)
    devices_to_test.append((None, None, "default device"))
    
    # 3. Try all input devices by index
    for idx, device in input_devices:
        name = device.get('name', 'Unknown')
        # Skip if already in list (from config preference)
        if not any(test_idx == idx for test_idx, _, _ in devices_to_test if test_idx is not None):
            devices_to_test.append((idx, device, f"device {idx}: {name}"))
    
    # Test each device
    last_error = None
    for device_id, device_info, description in devices_to_test:
        success, error = _test_device_stream(
            device_id,
            samplerate,
            channels,
            description
        )
        
        if success:
            # Device works! Extract device identifier to save
            if device_id is None:
                # Default device - save empty string
                device_identifier = ""
                logger.info("Microphone check OK: Default device works")
            else:
                # Specific device - save device name
                device_identifier = device_info.get('name', '') if device_info else ""
                logger.info(f"Microphone check OK: Device '{device_identifier}' works")
            
            return (True, None, device_identifier)
        else:
            last_error = error
    
    # All devices failed
    error_hint = last_error or "No working microphone device found"
    logger.error(f"Microphone check FAIL: {error_hint}")
    return (False, error_hint, None)


def _test_device_stream(
    device: Optional[int],
    samplerate: int,
    channels: int,
    description: str
) -> tuple[bool, Optional[str]]:
    """
    Test if a device can be opened for recording.
    
    Opens an InputStream briefly (≤300ms) to verify device access.
    
    Args:
        device: Device index or None for default
        samplerate: Sample rate to test (e.g., 16000)
        channels: Number of channels to test (e.g., 1)
        description: Human-readable device description for logging
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        import sounddevice as sd
        
        logger.info(f"Testing {description}...")
        
        # Try to open a short test stream
        # blocksize=1024 keeps the test quick
        stream = sd.InputStream(
            device=device,
            channels=channels,
            samplerate=samplerate,
            blocksize=1024,
        )
        
        # Open the stream (this is where permission/access is checked)
        stream.start()
        
        # Wait briefly to ensure stream is actually working
        # Per ticket spec: ≤300ms total test time
        time.sleep(0.1)  # 100ms
        
        # Close the stream
        stream.stop()
        stream.close()
        
        logger.info(f"✓ {description} - OK")
        return (True, None)
        
    except sd.PortAudioError as e:
        # Device unavailable, disabled, or permission denied
        error_msg = f"{description} - PortAudioError: {e}"
        logger.warning(error_msg)
        return (False, str(e))
        
    except PermissionError as e:
        # Explicit permission denied
        error_msg = f"{description} - Permission denied: {e}"
        logger.warning(error_msg)
        return (False, "Microphone access denied (check privacy settings)")
        
    except OSError as e:
        # General OS error (e.g., device disconnected)
        error_msg = f"{description} - OS error: {e}"
        logger.warning(error_msg)
        return (False, str(e))
        
    except Exception as e:
        # Unexpected error
        error_msg = f"{description} - Unexpected error: {type(e).__name__}: {e}"
        logger.warning(error_msg)
        return (False, f"{type(e).__name__}: {e}")


def get_device_index(config: AppConfig) -> Optional[int]:
    """
    Return sounddevice input device index for recording. None = default device.

    Args:
        config: AppConfig with audio.device ("" or device name substring)

    Returns:
        Device index or None to use default.
    """
    if not config.audio.device or not config.audio.device.strip():
        return None
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        needle = config.audio.device.strip().lower()
        for i, d in enumerate(devices):
            if isinstance(d, dict) and d.get("max_input_channels", 0) > 0:
                name = (d.get("name") or "").lower()
                if needle in name:
                    return i
    except Exception:
        pass
    return None
