from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

# Load environment variables once at application startup
load_dotenv()

from .config import get_default_output_dir, validate_spotify_env
from .recorder import run_session

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def run_session_cmd(
    ctx: typer.Context,
    output_dir: Path = typer.Option(
        get_default_output_dir(),
        help="Directory where session folders and data files will be stored.",
    ),
    pre_roll_sec: float = typer.Option(
        0.0,
        help="Seconds of data BEFORE detected Spotify play to keep (if available).",
    ),
):
    """
    Run a single Muse+Spotify synchronized recording session.
    """
    if ctx.invoked_subcommand is not None:
        return

    validate_spotify_env()
    run_session(output_dir=output_dir, pre_roll_sec=pre_roll_sec)


def main():
    app()


if __name__ == "__main__":
    main()