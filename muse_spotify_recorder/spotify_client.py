from __future__ import annotations

import time
from typing import Optional

import spotipy
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table
from spotipy.oauth2 import SpotifyOAuth

from pylsl import local_clock

from .models import RecordingConfig, RecordingState, SpotifyTrackInfo

console = Console()


def create_spotify_client() -> spotipy.Spotify:
    """
    Authenticate with Spotify using Spotipy's OAuth helper.
    """
    scope = "user-read-playback-state user-read-currently-playing"
    auth_manager = SpotifyOAuth(scope=scope, open_browser=True)
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playback(sp: spotipy.Spotify) -> Optional[dict]:
    """
    Safely fetch current playback info.
    """
    try:
        return sp.current_playback()
    except Exception as e:
        console.print(f"[red]Spotify API error:[/red] {e}")
        return None


def wait_for_spotify_play(
    sp: spotipy.Spotify,
    state: RecordingState,
    cfg: RecordingConfig,
) -> SpotifyTrackInfo:
    """
    Block until Spotify starts playing or the track changes while playing.

    Returns:
        SpotifyTrackInfo with timing metadata aligned to pylsl.local_clock().
    """
    console.rule("[bold green]Arm Recording[/bold green]")
    console.print(
        "[bold]Instructions:[/bold]\n"
        "1. Make sure Spotify is open on this machine.\n"
        "2. Pause playback before arming, if something is already playing.\n"
        "3. [green]Press Enter to arm[/green], then hit [green]Play[/green] in Spotify."
    )
    input("\nPress Enter to arm and then Play in Spotify...")

    last_track_id: Optional[str] = None
    last_is_playing: bool = False

    with Live(refresh_per_second=4, console=console) as live:
        while True:
            playback = get_playback(sp)
            now_lsl = local_clock()
            now_unix = time.time()

            table = Table(
                title="Waiting for Spotify playback...",
                box=box.SIMPLE,
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Status")
            table.add_column("Value")

            if playback and playback.get("item"):
                is_playing = playback.get("is_playing", False)
                item = playback["item"]
                track_id = item["id"]
                track_name = item["name"]
                artists = ", ".join(a["name"] for a in item.get("artists", []))
                album = item["album"]["name"]
                duration_ms = item["duration_ms"]
                progress_ms = playback.get("progress_ms", 0) or 0

                table.add_row("Track", f"{track_name} — {artists}")
                table.add_row("Album", album)
                table.add_row("Duration", f"{duration_ms/1000:.1f} s")
                table.add_row("Position", f"{progress_ms/1000:.1f} s")
                table.add_row("State", "▶️ playing" if is_playing else "⏸ paused")

                play_started = False
                if not last_is_playing and is_playing:
                    play_started = True
                elif is_playing and last_track_id and track_id != last_track_id:
                    play_started = True

                last_is_playing = is_playing
                last_track_id = track_id

                if play_started:
                    live.update(table)
                    console.print(
                        "\n[bold green]Detected playback start.[/bold green] "
                        "Aligning Muse data to this moment (t = 0)."
                    )

                    track_info = SpotifyTrackInfo(
                        track_id=track_id,
                        track_name=track_name,
                        artist_name=artists,
                        album_name=album,
                        duration_ms=duration_ms,
                        started_at_unix=now_unix,
                        started_at_lsl=now_lsl,
                        playback_position_ms=progress_ms,
                    )
                    state.play_detected = True
                    state.track_info = track_info
                    return track_info
            else:
                table.add_row("Playback", "No active device / nothing playing")

            live.update(table)
            time.sleep(cfg.poll_interval_sec)
