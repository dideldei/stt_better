"""
Configuration loader for STT-Diktat-Agent.

Loads and validates config.toml from the project root.
Handles errors with clean exit.
"""

import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass

try:
    import tomllib
except ImportError:
    # Fallback for Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: tomllib (Python 3.11+) or tomli required for config loading")
        sys.exit(1)


@dataclass
class AudioConfig:
    """Audio configuration"""
    device: str
    samplerate: int
    channels: int


@dataclass
class SnippetConfig:
    """Snippet configuration"""
    seconds: int


@dataclass
class STTConfig:
    """STT configuration"""
    model: str
    compute_type: str
    beam_size: int
    language: str
    initial_prompt: str | None = None  # optional; default when missing from config


@dataclass
class RetentionConfig:
    """Retention configuration"""
    recordings_days: int
    logs_days: int


@dataclass
class AppConfig:
    """Complete application configuration"""
    audio: AudioConfig
    snippet: SnippetConfig
    stt: STTConfig
    retention: RetentionConfig


def load_config(config_path: Path | None = None) -> AppConfig:
    """
    Load and validate config.toml.
    
    Args:
        config_path: Path to config.toml. If None, uses project root.
    
    Returns:
        AppConfig with validated values.
    
    Exits:
        sys.exit(1) with error message if config is invalid or missing.
    """
    if config_path is None:
        # Assume config.toml is in project root (parent of util/)
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.toml"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse config.toml: {e}")
        sys.exit(1)
    
    # Validate required sections
    required_sections = ["audio", "snippet", "stt", "retention"]
    for section in required_sections:
        if section not in config_data:
            print(f"ERROR: Missing required section '[{section}]' in config.toml")
            sys.exit(1)
    
    # Validate and extract audio config
    audio_data = config_data["audio"]
    required_audio_keys = ["device", "samplerate", "channels"]
    for key in required_audio_keys:
        if key not in audio_data:
            print(f"ERROR: Missing required key 'audio.{key}' in config.toml")
            sys.exit(1)
    
    try:
        audio = AudioConfig(
            device=str(audio_data["device"]),
            samplerate=int(audio_data["samplerate"]),
            channels=int(audio_data["channels"])
        )
    except (ValueError, TypeError) as e:
        print(f"ERROR: Invalid audio configuration: {e}")
        sys.exit(1)
    
    # Validate and extract snippet config
    snippet_data = config_data["snippet"]
    if "seconds" not in snippet_data:
        print("ERROR: Missing required key 'snippet.seconds' in config.toml")
        sys.exit(1)
    
    try:
        snippet = SnippetConfig(
            seconds=int(snippet_data["seconds"])
        )
    except (ValueError, TypeError) as e:
        print(f"ERROR: Invalid snippet configuration: {e}")
        sys.exit(1)
    
    # Validate and extract STT config
    stt_data = config_data["stt"]
    required_stt_keys = ["model", "compute_type", "beam_size", "language"]
    for key in required_stt_keys:
        if key not in stt_data:
            print(f"ERROR: Missing required key 'stt.{key}' in config.toml")
            sys.exit(1)
    
    # Optional: initial_prompt (default None when missing or empty)
    _raw = stt_data.get("initial_prompt")
    if _raw is None:
        initial_prompt = None
    else:
        _s = str(_raw).strip()
        initial_prompt = _s if _s else None

    try:
        stt = STTConfig(
            model=str(stt_data["model"]),
            compute_type=str(stt_data["compute_type"]),
            beam_size=int(stt_data["beam_size"]),
            language=str(stt_data["language"]),
            initial_prompt=initial_prompt,
        )
    except (ValueError, TypeError) as e:
        print(f"ERROR: Invalid STT configuration: {e}")
        sys.exit(1)
    
    # Validate and extract retention config
    retention_data = config_data["retention"]
    required_retention_keys = ["recordings_days", "logs_days"]
    for key in required_retention_keys:
        if key not in retention_data:
            print(f"ERROR: Missing required key 'retention.{key}' in config.toml")
            sys.exit(1)
    
    try:
        retention = RetentionConfig(
            recordings_days=int(retention_data["recordings_days"]),
            logs_days=int(retention_data["logs_days"])
        )
    except (ValueError, TypeError) as e:
        print(f"ERROR: Invalid retention configuration: {e}")
        sys.exit(1)
    
    return AppConfig(
        audio=audio,
        snippet=snippet,
        stt=stt,
        retention=retention
    )
