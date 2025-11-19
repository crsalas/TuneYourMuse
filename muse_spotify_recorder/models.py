from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pylsl import StreamInlet


@dataclass
class StreamConfig:
    lsl_type: str
    filename: str
    inlet: Optional[StreamInlet] = None


@dataclass
class RecordingConfig:
    output_dir: Path
    pre_roll_sec: float = 0.0
    post_roll_sec: float = 0.0
    poll_interval_sec: float = 0.25

    def to_dict(self) -> Dict:
        return {
            "output_dir": str(self.output_dir),
            "pre_roll_sec": self.pre_roll_sec,
            "post_roll_sec": self.post_roll_sec,
            "poll_interval_sec": self.poll_interval_sec,
        }


@dataclass
class SpotifyTrackInfo:
    track_id: str
    track_name: str
    artist_name: str
    album_name: str
    duration_ms: int
    started_at_unix: float
    started_at_lsl: float
    playback_position_ms: int

    def to_dict(self) -> Dict:
        return {
            "track_id": self.track_id,
            "track_name": self.track_name,
            "artist_name": self.artist_name,
            "album_name": self.album_name,
            "duration_ms": self.duration_ms,
            "started_at_unix": self.started_at_unix,
            "started_at_lsl": self.started_at_lsl,
            "playback_position_ms": self.playback_position_ms,
        }


@dataclass
class RecordingState:
    should_stop: bool = False
    play_detected: bool = False
    track_info: Optional[SpotifyTrackInfo] = None


def generate_session_id() -> str:
    """Generate a unique session id."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
