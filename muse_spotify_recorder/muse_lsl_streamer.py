"""Muse LSL (Lab Streaming Layer) streamer.

This module manages LSL outlets for streaming Muse sensor data (EEG, ACC, GYRO)
to the Lab Streaming Layer network. Other applications can discover and subscribe
to these streams for real-time data processing and recording.
"""

from typing import Optional, List
import numpy as np
import pylsl
from rich.console import Console

from .config import MUSE_NAME
from .muse_constants import (
    LSL_EEG_NAME,
    LSL_EEG_TYPE,
    LSL_ACC_NAME,
    LSL_ACC_TYPE,
    LSL_GYRO_NAME,
    LSL_GYRO_TYPE,
    EEG_SAMPLE_RATE,
    EEG_CHANNEL_COUNT,
    EEG_CHANNEL_NAMES,
    ACC_SAMPLE_RATE,
    ACC_CHANNEL_COUNT,
    GYRO_SAMPLE_RATE,
    GYRO_CHANNEL_COUNT,
)

console = Console()


class MuseLSLStreamer:
    """Manages LSL outlets for Muse sensor streams.

    This class creates and manages three LSL StreamOutlets:
    - EEG: 4 channels at 256 Hz (TP9, AF7, AF8, TP10)
    - Accelerometer: 3 channels at ~52 Hz (X, Y, Z)
    - Gyroscope: 3 channels at ~52 Hz (X, Y, Z)

    Each stream has metadata describing the channels and units.
    """

    def __init__(self, muse_name: str = MUSE_NAME):
        """Initialize the LSL streamer.

        Args:
            muse_name: Name of the Muse device (for stream source ID)
        """
        self.muse_name = muse_name
        self.eeg_outlet: Optional[pylsl.StreamOutlet] = None
        self.acc_outlet: Optional[pylsl.StreamOutlet] = None
        self.gyro_outlet: Optional[pylsl.StreamOutlet] = None

        self._streams_created = False

    def create_streams(self) -> None:
        """Create all LSL StreamOutlets.

        This should be called once before pushing any samples.
        Creates three LSL streams with appropriate metadata.
        """
        if self._streams_created:
            console.print("[yellow]LSL streams already created, skipping...[/yellow]")
            return

        console.print("[cyan]Creating LSL streams...[/cyan]")

        # Create EEG stream
        eeg_info = pylsl.StreamInfo(
            name=LSL_EEG_NAME,
            type=LSL_EEG_TYPE,
            channel_count=EEG_CHANNEL_COUNT,
            nominal_srate=EEG_SAMPLE_RATE,
            channel_format=pylsl.cf_float32,
            source_id=f"{self.muse_name}_eeg"
        )

        # Add EEG channel metadata
        channels = eeg_info.desc().append_child("channels")
        for ch_name in EEG_CHANNEL_NAMES:
            ch = channels.append_child("channel")
            ch.append_child_value("label", ch_name)
            ch.append_child_value("unit", "microvolts")
            ch.append_child_value("type", "EEG")

        self.eeg_outlet = pylsl.StreamOutlet(eeg_info, chunk_size=12, max_buffered=360)
        console.print(f"  ✓ Created EEG stream: {EEG_CHANNEL_COUNT} channels @ {EEG_SAMPLE_RATE} Hz")

        # Create Accelerometer stream
        acc_info = pylsl.StreamInfo(
            name=LSL_ACC_NAME,
            type=LSL_ACC_TYPE,
            channel_count=ACC_CHANNEL_COUNT,
            nominal_srate=ACC_SAMPLE_RATE,
            channel_format=pylsl.cf_float32,
            source_id=f"{self.muse_name}_acc"
        )

        # Add ACC channel metadata
        channels = acc_info.desc().append_child("channels")
        for axis in ["X", "Y", "Z"]:
            ch = channels.append_child("channel")
            ch.append_child_value("label", f"ACC_{axis}")
            ch.append_child_value("unit", "g")
            ch.append_child_value("type", "Accelerometer")

        self.acc_outlet = pylsl.StreamOutlet(acc_info, chunk_size=3, max_buffered=360)
        console.print(f"  ✓ Created ACC stream: {ACC_CHANNEL_COUNT} channels @ {ACC_SAMPLE_RATE} Hz")

        # Create Gyroscope stream
        gyro_info = pylsl.StreamInfo(
            name=LSL_GYRO_NAME,
            type=LSL_GYRO_TYPE,
            channel_count=GYRO_CHANNEL_COUNT,
            nominal_srate=GYRO_SAMPLE_RATE,
            channel_format=pylsl.cf_float32,
            source_id=f"{self.muse_name}_gyro"
        )

        # Add GYRO channel metadata
        channels = gyro_info.desc().append_child("channels")
        for axis in ["X", "Y", "Z"]:
            ch = channels.append_child("channel")
            ch.append_child_value("label", f"GYRO_{axis}")
            ch.append_child_value("unit", "deg/s")
            ch.append_child_value("type", "Gyroscope")

        self.gyro_outlet = pylsl.StreamOutlet(gyro_info, chunk_size=3, max_buffered=360)
        console.print(f"  ✓ Created GYRO stream: {GYRO_CHANNEL_COUNT} channels @ {GYRO_SAMPLE_RATE} Hz")

        self._streams_created = True
        console.print("[green]✓ All LSL streams created successfully![/green]\n")

    def push_eeg_chunk(self, samples: np.ndarray, timestamp: Optional[float] = None) -> None:
        """Push a chunk of EEG samples to the LSL stream.

        Args:
            samples: numpy array of shape (n_samples, 4) or (12, 4) for 12 samples × 4 channels
                     Values should be in microvolts (µV)
            timestamp: Optional LSL timestamp (uses current time if None)

        Raises:
            RuntimeError: If streams haven't been created yet
        """
        if not self._streams_created or self.eeg_outlet is None:
            raise RuntimeError("LSL streams not created. Call create_streams() first.")

        if timestamp is None:
            timestamp = pylsl.local_clock()

        # Push each sample with appropriate timestamp
        # If we have 12 samples at 256 Hz, they span 12/256 = 0.046875 seconds
        if samples.shape[0] > 1:
            time_per_sample = 1.0 / EEG_SAMPLE_RATE
            for i, sample in enumerate(samples):
                sample_timestamp = timestamp + (i * time_per_sample)
                self.eeg_outlet.push_sample(sample.tolist(), sample_timestamp)
        else:
            self.eeg_outlet.push_sample(samples[0].tolist(), timestamp)

    def push_acc_chunk(self, samples: np.ndarray, timestamp: Optional[float] = None) -> None:
        """Push accelerometer samples to the LSL stream.

        Args:
            samples: numpy array of shape (n_samples, 3) - typically (3, 3) for 3 samples × 3 axes
                     Values should be in g (gravitational acceleration)
            timestamp: Optional LSL timestamp (uses current time if None)

        Raises:
            RuntimeError: If streams haven't been created yet
        """
        if not self._streams_created or self.acc_outlet is None:
            raise RuntimeError("LSL streams not created. Call create_streams() first.")

        if timestamp is None:
            timestamp = pylsl.local_clock()

        # Push each sample with appropriate timestamp
        if samples.shape[0] > 1:
            time_per_sample = 1.0 / ACC_SAMPLE_RATE
            for i, sample in enumerate(samples):
                sample_timestamp = timestamp + (i * time_per_sample)
                self.acc_outlet.push_sample(sample.tolist(), sample_timestamp)
        else:
            self.acc_outlet.push_sample(samples[0].tolist(), timestamp)

    def push_gyro_chunk(self, samples: np.ndarray, timestamp: Optional[float] = None) -> None:
        """Push gyroscope samples to the LSL stream.

        Args:
            samples: numpy array of shape (n_samples, 3) - typically (3, 3) for 3 samples × 3 axes
                     Values should be in deg/s (degrees per second)
            timestamp: Optional LSL timestamp (uses current time if None)

        Raises:
            RuntimeError: If streams haven't been created yet
        """
        if not self._streams_created or self.gyro_outlet is None:
            raise RuntimeError("LSL streams not created. Call create_streams() first.")

        if timestamp is None:
            timestamp = pylsl.local_clock()

        # Push each sample with appropriate timestamp
        if samples.shape[0] > 1:
            time_per_sample = 1.0 / GYRO_SAMPLE_RATE
            for i, sample in enumerate(samples):
                sample_timestamp = timestamp + (i * time_per_sample)
                self.gyro_outlet.push_sample(sample.tolist(), sample_timestamp)
        else:
            self.gyro_outlet.push_sample(samples[0].tolist(), timestamp)

    def close_streams(self) -> None:
        """Cleanup and close all LSL outlets.

        This should be called when streaming is finished.
        """
        if not self._streams_created:
            return

        console.print("[cyan]Closing LSL streams...[/cyan]")

        # LSL outlets are automatically cleaned up when deleted
        self.eeg_outlet = None
        self.acc_outlet = None
        self.gyro_outlet = None

        self._streams_created = False
        console.print("[green]✓ LSL streams closed[/green]")

    def is_ready(self) -> bool:
        """Check if all streams are created and ready to push samples.

        Returns:
            True if all outlets are created, False otherwise
        """
        return (
            self._streams_created
            and self.eeg_outlet is not None
            and self.acc_outlet is not None
            and self.gyro_outlet is not None
        )
