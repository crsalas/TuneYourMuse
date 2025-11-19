from __future__ import annotations

import os
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()

# LSL stream types we care about
# Note: PPG removed assome Muse headsets don't have PPG sensors
LSL_TYPES: List[str] = ["EEG", "ACC", "GYRO"]

MUSE_NAME = os.getenv("MUSE_NAME")
if not MUSE_NAME:
    raise ValueError("MUSE_NAME is not set in .env file")


def get_default_output_dir() -> Path:
    return Path("./recordings").expanduser().resolve()


def validate_spotify_env() -> None:
    """
    Optional helper to sanity check Spotify env vars.
    Not strictly required because Spotipy can also read them,
    but this gives nicer CLI UX if something's obviously missing.
    """
    missing = []
    if not os.getenv("SPOTIPY_CLIENT_ID"):
        missing.append("SPOTIPY_CLIENT_ID")
    if not os.getenv("SPOTIPY_CLIENT_SECRET"):
        missing.append("SPOTIPY_CLIENT_SECRET")
    if not os.getenv("SPOTIPY_REDIRECT_URI"):
        missing.append("SPOTIPY_REDIRECT_URI")

    if missing:
        console.print(
            "[yellow]Warning:[/yellow] The following Spotify env vars are not set:\n"
            f"  {', '.join(missing)}\n"
            "Spotipy will still prompt you in the browser, but it's recommended to set them."
        )
