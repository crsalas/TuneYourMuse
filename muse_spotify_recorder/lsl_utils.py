from __future__ import annotations

import csv
import time
from typing import Dict, List

from pylsl import StreamInlet, resolve_streams
from rich import box
from rich.console import Console
from rich.table import Table

from .models import RecordingConfig, RecordingState, StreamConfig

console = Console()


def wait_for_lsl_streams(
    lsl_types: List[str],
    timeout: float = 15.0,
) -> Dict[str, StreamInlet]:
    """
    Wait for specific LSL stream types (e.g., 'EEG', 'ACC', 'GYRO', 'PPG').

    Returns:
        Dict of stream_type -> StreamInlet.
    Raises:
        RuntimeError if mandatory EEG stream is not found.
    """
    found: Dict[str, StreamInlet] = {}
    start = time.time()

    while time.time() - start < timeout and len(found) < len(lsl_types):
        all_streams = resolve_streams()  # discover all
        for info in all_streams:
            stype = info.type()
            if stype in lsl_types and stype not in found:
                found[stype] = StreamInlet(info, max_buflen=60)
        if len(found) < len(lsl_types):
            time.sleep(1.0)

    if "EEG" not in found:
        raise RuntimeError("Could not find EEG LSL stream from Muse. Is the headset streaming?")

    return found


def basic_connection_health_check(eeg_inlet: StreamInlet, duration_sec: float = 5.0) -> None:
    """
    Pull samples from EEG inlet for a short period and show basic stats.

    This is a rough health check (not a full impedance / quality metric).
    """
    console.rule("[bold cyan]Muse Connection Health Check[/bold cyan]")
    console.print("Collecting a few seconds of EEG data to sanity-check the connection...")

    samples = []
    end_time = time.time() + duration_sec
    while time.time() < end_time:
        chunk, ts = eeg_inlet.pull_chunk(timeout=0.5)
        if chunk:
            samples.extend(chunk)

    if not samples:
        console.print("[red]No EEG samples received during health check.[/red]")
        return

    num_channels = len(samples[0])
    variances = []
    for ch in range(num_channels):
        vals = [s[ch] for s in samples]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
        variances.append(var)

    table = Table(
        title="EEG Channel Variance (rough connectivity proxy)",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Channel Index")
    table.add_column("Variance (approx)")
    for idx, var in enumerate(variances):
        status = "[green]OK[/green]" if var > 1e-6 else "[red]very low[/red]"
        table.add_row(str(idx), f"{var:.3e} {status}")

    console.print(table)
    console.print(
        "\n[bold]Tip:[/bold] If channels look 'very low', adjust the headband / hair and rerun."
    )


# def _open_stream_writers(
#     stream_cfgs: Dict[str, StreamConfig],
# ) -> Dict[str, csv.writer]:
#     """
#     Open CSV files for each stream, attach file handles to inlets.
#     """
#     writers: Dict[str, csv.writer] = {}
#     for stype, cfg in stream_cfgs.items():
#         path = cfg.filename
#         f = open(path, "w", newline="")
#         writer = csv.writer(f)
#         writer.writerow(["sample_index", "lsl_timestamp", "time_since_play_sec", "channels..."])
#         writers[stype] = writer
#         cfg.inlet._file_handle = f  # type: ignore[attr-defined]
#     return writers

def _open_stream_writers(
    stream_cfgs: Dict[str, StreamConfig],
) -> Dict[str, csv.writer]:
    """
    Open CSV files for each stream, attach file handles to inlets.
    """
    writers: Dict[str, csv.writer] = {}
    for stype, cfg in stream_cfgs.items():
        path = cfg.filename
        f = open(path, "w", newline="")
        writer = csv.writer(f)

        # --- CORRECTED HEADER LOGIC ---
        # Define base header
        header = ["sample_index", "lsl_timestamp", "time_since_play_sec"]

        # Add channel names based on stream type
        # These names are based on muse_constants.py and muse_lsl_streamer.py
        if stype == "EEG":
            header.extend(["TP9", "AF7", "AF8", "TP10"])
        elif stype == "ACC":
            header.extend(["ACC_X", "ACC_Y", "ACC_Z"])
        elif stype == "GYRO":
            header.extend(["GYRO_X", "GYRO_Y", "GYRO_Z"])
        else:
            # Fallback for unknown stream types
            try:
                if cfg.inlet:
                    info = cfg.inlet.info()
                    header.extend([f"ch{i+1}" for i in range(info.channel_count())])
                else:
                    header.append("channels...") # Failsafe
            except Exception:
                header.append("channels...") # Failsafe

        # Write the new, correct header
        writer.writerow(header)
        # --- END OF CORRECTION ---

        writers[stype] = writer
        if cfg.inlet:
            cfg.inlet._file_handle = f  # type: ignore[attr-defined]
            
    return writers


def _close_stream_writers(stream_cfgs: Dict[str, StreamConfig]) -> None:
    for cfg in stream_cfgs.values():
        fh = getattr(cfg.inlet, "_file_handle", None)
        if fh is not None:
            fh.close()


def recording_loop(
    state: RecordingState,
    cfg: RecordingConfig,
    stream_cfgs: Dict[str, StreamConfig],
) -> None:
    """
    Pull from LSL inlets and write to CSVs.

    - Blocks until state.track_info is set.
    - Aligns timestamps to the LSL time at Spotify play (t=0).
    """
    if not state.track_info:
        raise RuntimeError("Recording loop started without track_info set.")

    play_lsl = state.track_info.started_at_lsl
    pre_roll = cfg.pre_roll_sec

    # Update filenames to include full session path
    for scfg in stream_cfgs.values():
        scfg.filename = str(cfg.output_dir / scfg.filename)

    writers = _open_stream_writers(stream_cfgs)
    sample_indices = {k: 0 for k in stream_cfgs.keys()}

    console.rule("[bold green]Recording[/bold green]")
    console.print(
        f"Recording Muse data aligned to Spotify track:\n"
        f"[bold]{state.track_info.track_name}[/bold] — {state.track_info.artist_name}\n"
        f"t = 0 at detected playback time. Press [yellow]Ctrl+C[/yellow] to stop.\n"
    )

    try:
        while not state.should_stop:
            for stype, scfg in stream_cfgs.items():
                inlet = scfg.inlet
                writer = writers[stype]
                if inlet is None:
                    continue

                chunk, ts = inlet.pull_chunk(timeout=0.0)
                if not chunk:
                    continue

                for sample, tstamp in zip(chunk, ts):
                    rel_t = tstamp - play_lsl
                    if rel_t < -pre_roll:
                        continue
                    idx = sample_indices[stype]
                    row = [idx, tstamp, rel_t] + list(sample)
                    writer.writerow(row)
                    sample_indices[stype] += 1

            time.sleep(0.01)
    finally:
        _close_stream_writers(stream_cfgs)
