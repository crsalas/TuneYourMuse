from __future__ import annotations

import asyncio
import atexit
import json
import os
import signal
import threading
from pathlib import Path
from typing import Dict, Optional

import typer
from rich.console import Console

from .config import LSL_TYPES, MUSE_NAME
from .lsl_utils import basic_connection_health_check, recording_loop, wait_for_lsl_streams
from .models import RecordingConfig, RecordingState, StreamConfig, generate_session_id
from .custom_muse_streamer import CustomMuseStreamer
from .spotify_client import create_spotify_client, wait_for_spotify_play

console = Console()


class MuseStreamerThread:
    """Manages CustomMuseStreamer in a background thread."""

    def __init__(self, device_address: str, muse_name: str):
        self.device_address = device_address
        self.muse_name = muse_name
        self.streamer: Optional[CustomMuseStreamer] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._started_event = threading.Event()

    def start(self) -> bool:
        """Start the Muse streamer in a background thread."""
        if self._started_event.is_set():
            return True

        self.streamer = CustomMuseStreamer(self.device_address, self.muse_name)

        def run_async_streamer():
            """Run the async streamer in a background thread."""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            try:
                # Start the streamer
                if self.loop.run_until_complete(self.streamer.start()):
                    self._running = True
                    self._started_event.set()

                    # Keep running until terminated
                    while self._running:
                        self.loop.run_until_complete(asyncio.sleep(0.1))

            except Exception as e:
                console.print(f"[red]Error in Muse streamer: {e}[/red]")
                self._started_event.set()
            finally:
                # Cleanup
                if self.streamer and self.streamer.is_running():
                    self.loop.run_until_complete(self.streamer.stop())
                self.loop.close()

        # Start in background thread
        self.thread = threading.Thread(target=run_async_streamer, daemon=True)
        self.thread.start()

        # Wait for the streamer to start
        started = self._started_event.wait(timeout=15.0)
        return started and self._running

    def terminate(self) -> None:
        """Stop the Muse streamer."""
        if not self._running:
            return

        self._running = False

        # Stop the streamer
        if self.loop and self.streamer:
            asyncio.run_coroutine_threadsafe(self.streamer.stop(), self.loop)

        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=5.0)

    def poll(self) -> Optional[int]:
        """Check if still running."""
        if self._running and self.thread and self.thread.is_alive():
            return None
        return 0


def run_session(
    output_dir: Path,
    pre_roll_sec: float = 0.0,
) -> None:
    """
    Execute a full Muse+Spotify synchronized recording session.
    """
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    console.rule("[bold blue]Muse 2 + Spotify Recorder[/bold blue]")

    # --- Start Muse Stream ---
    console.print("[bold cyan]Starting Custom Muse LSL stream...[/bold cyan]")

    device_address = os.getenv("DEVICE_MAC_ADDRESS")
    if not device_address:
        console.print("[red]Error: DEVICE_MAC_ADDRESS not set in .env file[/red]")
        raise typer.Exit(code=1)

    muse_proc = MuseStreamerThread(device_address, MUSE_NAME)

    if not muse_proc.start():
        console.print("[red]Failed to start Muse streamer[/red]")
        raise typer.Exit(code=1)

    # Register cleanup on exit
    atexit.register(muse_proc.terminate)

    console.print("[green]✓ Muse streamer started successfully[/green]\n")

    # --- LSL streams ---
    try:
        found_inlets = wait_for_lsl_streams(LSL_TYPES)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        muse_proc.terminate()
        raise typer.Exit(code=1)

    console.print("\n[green]Connected to Muse LSL streams:[/green]")
    for stype, inlet in found_inlets.items():
        info = inlet.info()
        console.print(f" - {stype}: {info.name()} @ {info.nominal_srate()} Hz")

    # Health check
    basic_connection_health_check(found_inlets["EEG"])

    # --- Spotify client ---
    console.rule("[bold blue]Spotify Setup[/bold blue]")
    console.print(
        "Setting up Spotify client. If prompted, log in and approve access.\n"
        "Scopes: [cyan]user-read-playback-state[/cyan], [cyan]user-read-currently-playing[/cyan]."
    )
    sp = create_spotify_client()
    me = sp.current_user()
    console.print(f"Authenticated as Spotify user: [bold]{me['display_name']}[/bold]\n")

    # --- Prepare session ---
    session_id = generate_session_id()
    session_dir = output_dir / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=False)

    rec_cfg = RecordingConfig(
        output_dir=session_dir,
        pre_roll_sec=pre_roll_sec,
    )
    state = RecordingState()

    # --- Wait for Spotify play event ---
    track_info = wait_for_spotify_play(sp, state, rec_cfg)
    state.track_info = track_info

    # --- Stream configs ---
    stream_cfgs: Dict[str, StreamConfig] = {}
    for stype, inlet in found_inlets.items():
        filename = f"{stype.lower()}_samples.csv"
        stream_cfgs[stype] = StreamConfig(
            lsl_type=stype,
            filename=filename,
            inlet=inlet,
        )

    # --- Metadata ---
    device_address = os.getenv("DEVICE_MAC_ADDRESS", "N/A")

    meta = {
        "session_id": session_id,
        "muse": {
            "name": f"Custom Muse Streamer ({MUSE_NAME})",
            "address": device_address,
            "implementation": "bleak + pylsl (custom)",
        },
        "spotify": track_info.to_dict(),
        "recording_config": rec_cfg.to_dict(),
        "streams": list(stream_cfgs.keys()),
    }
    with open(session_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    # --- Signal handling & recording ---
    def handle_sigint(signum, frame):
        console.print("\n[yellow]Stopping recording...[/yellow]")
        state.should_stop = True

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        recording_loop(state, rec_cfg, stream_cfgs)
    finally:
        if muse_proc.poll() is None:
            muse_proc.terminate()
        console.print(
            f"\n[bold green]Session complete.[/bold green] Data stored in: [cyan]{session_dir}[/cyan]"
        )