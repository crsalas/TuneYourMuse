"""Custom Muse streamer using bleak and pylsl.

This module coordinates the BLE connection to the Muse headband and streams
sensor data to LSL (Lab Streaming Layer). It replaces the muselsl-based
implementation which had connection issues.

Architecture:
- MuseBLEClient: Handles BLE connection and subscriptions
- MuseLSLStreamer: Manages LSL outlets for EEG, ACC, GYRO
- Parser functions: Convert raw BLE packets to calibrated values
- CustomMuseStreamer: Coordinates everything and manages the data flow
"""

import asyncio
from typing import Optional, Dict
import numpy as np
import pylsl
from rich.console import Console

from .config import MUSE_NAME
from .muse_bluetooth import MuseBLEClient
from .muse_lsl_streamer import MuseLSLStreamer
from .muse_parser import parse_eeg_packet, parse_acc_packet, parse_gyro_packet

console = Console()


class CustomMuseStreamer:
    """Main coordinator for Muse BLE → LSL streaming.

    This class integrates the BLE client, LSL streamer, and packet parsers
    to create a complete streaming pipeline from the Muse headband to LSL.

    Usage:
        streamer = CustomMuseStreamer(device_address="XX:XX:XX:XX:XX:XX")
        await streamer.start()
        # ... streaming happens ...
        await streamer.stop()
    """

    def __init__(self, device_address: str, muse_name: str = MUSE_NAME):
        """Initialize the custom Muse streamer.

        Args:
            device_address: MAC address of the Muse device
            muse_name: Name of the Muse device
        """
        self.device_address = device_address
        self.muse_name = muse_name

        # Create components
        self.ble_client = MuseBLEClient(device_address, muse_name)
        self.lsl_streamer = MuseLSLStreamer(muse_name)

        # State
        self._running = False
        self._keep_alive_task: Optional[asyncio.Task] = None

        # Packet counters for monitoring
        self._packet_counts = {
            "TP9": 0,
            "AF7": 0,
            "AF8": 0,
            "TP10": 0,
            "ACC": 0,
            "GYRO": 0,
        }

        # EEG packet buffer for synchronization
        # Maps packet_index -> {"TP9": samples, "AF7": samples, ...}
        self._eeg_buffer: Dict[int, Dict[str, np.ndarray]] = {}
        self._eeg_timestamps: Dict[int, float] = {}

    # EEG Synchronization
    def _process_eeg_packet(self, channel: str, packet_index: int, samples: np.ndarray) -> None:
        """Process an EEG packet and synchronize across channels.

        Args:
            channel: Channel name ("TP9", "AF7", "AF8", "TP10")
            packet_index: Packet sequence number
            samples: Array of 12 EEG samples for this channel
        """
        # Store in buffer
        if packet_index not in self._eeg_buffer:
            self._eeg_buffer[packet_index] = {}
            self._eeg_timestamps[packet_index] = pylsl.local_clock()

        self._eeg_buffer[packet_index][channel] = samples

        # Check if we have all 4 channels for this packet
        if len(self._eeg_buffer[packet_index]) == 4:
            # Combine all channels (shape: 12 samples × 4 channels)
            combined = np.column_stack([
                self._eeg_buffer[packet_index]["TP9"],
                self._eeg_buffer[packet_index]["AF7"],
                self._eeg_buffer[packet_index]["AF8"],
                self._eeg_buffer[packet_index]["TP10"],
            ])

            # Push to LSL
            timestamp = self._eeg_timestamps[packet_index]
            self.lsl_streamer.push_eeg_chunk(combined, timestamp)

            # Cleanup old buffers (keep only last 10 packets)
            if len(self._eeg_buffer) > 10:
                oldest_indices = sorted(self._eeg_buffer.keys())[:-10]
                for old_idx in oldest_indices:
                    del self._eeg_buffer[old_idx]
                    if old_idx in self._eeg_timestamps:
                        del self._eeg_timestamps[old_idx]

    # BLE Notification Callbacks
    def _on_eeg_tp9_data(self, sender, data: bytearray) -> None:
        """Callback for EEG TP9 notifications."""
        try:
            packet_index, samples = parse_eeg_packet(bytes(data))
            self._process_eeg_packet("TP9", packet_index, samples)
            self._packet_counts["TP9"] += 1
        except Exception as e:
            console.print(f"[red]Error parsing EEG TP9: {e}[/red]")

    def _on_eeg_af7_data(self, sender, data: bytearray) -> None:
        """Callback for EEG AF7 notifications."""
        try:
            packet_index, samples = parse_eeg_packet(bytes(data))
            self._process_eeg_packet("AF7", packet_index, samples)
            self._packet_counts["AF7"] += 1
        except Exception as e:
            console.print(f"[red]Error parsing EEG AF7: {e}[/red]")

    def _on_eeg_af8_data(self, sender, data: bytearray) -> None:
        """Callback for EEG AF8 notifications."""
        try:
            packet_index, samples = parse_eeg_packet(bytes(data))
            self._process_eeg_packet("AF8", packet_index, samples)
            self._packet_counts["AF8"] += 1
        except Exception as e:
            console.print(f"[red]Error parsing EEG AF8: {e}[/red]")

    def _on_eeg_tp10_data(self, sender, data: bytearray) -> None:
        """Callback for EEG TP10 notifications."""
        try:
            packet_index, samples = parse_eeg_packet(bytes(data))
            self._process_eeg_packet("TP10", packet_index, samples)
            self._packet_counts["TP10"] += 1
        except Exception as e:
            console.print(f"[red]Error parsing EEG TP10: {e}[/red]")

    def _on_acc_data(self, sender, data: bytearray) -> None:
        """Callback for Accelerometer notifications."""
        try:
            packet_index, samples = parse_acc_packet(bytes(data))
            timestamp = pylsl.local_clock()

            # Push 3 samples to LSL
            self.lsl_streamer.push_acc_chunk(samples, timestamp)
            self._packet_counts["ACC"] += 1

        except Exception as e:
            console.print(f"[red]Error parsing ACC: {e}[/red]")

    def _on_gyro_data(self, sender, data: bytearray) -> None:
        """Callback for Gyroscope notifications."""
        try:
            packet_index, samples = parse_gyro_packet(bytes(data))
            timestamp = pylsl.local_clock()

            # Push 3 samples to LSL
            self.lsl_streamer.push_gyro_chunk(samples, timestamp)
            self._packet_counts["GYRO"] += 1

        except Exception as e:
            console.print(f"[red]Error parsing GYRO: {e}[/red]")

    # Keep-Alive Task
    async def _keep_alive_loop(self) -> None:
        """Periodically send keep-alive commands to maintain connection."""
        while self._running:
            await asyncio.sleep(5.0)  # Send keep-alive every 5 seconds
            if self._running:
                await self.ble_client.keep_alive()

    # Main Control Methods
    async def start(self) -> bool:
        """Start the Muse streamer.

        This:
        1. Connects to the Muse via BLE
        2. Creates LSL outlets
        3. Subscribes to sensor notifications
        4. Sends control commands to start streaming
        5. Starts keep-alive task

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            console.print("[yellow]Streamer already running[/yellow]")
            return True

        console.print(f"[bold cyan]Starting Custom Muse Streamer[/bold cyan]\n")

        # 1. Connect to Muse
        if not await self.ble_client.connect():
            return False

        # 2. Create LSL outlets
        self.lsl_streamer.create_streams()

        # 3. Subscribe to sensors
        eeg_callbacks = {
            "TP9": self._on_eeg_tp9_data,
            "AF7": self._on_eeg_af7_data,
            "AF8": self._on_eeg_af8_data,
            "TP10": self._on_eeg_tp10_data,
        }

        if not await self.ble_client.subscribe_to_sensors(
            eeg_callbacks=eeg_callbacks,
            acc_callback=self._on_acc_data,
            gyro_callback=self._on_gyro_data
        ):
            await self.ble_client.disconnect()
            return False

        # 4. Start streaming
        if not await self.ble_client.start_streaming():
            await self.ble_client.disconnect()
            return False

        # 5. Start keep-alive task
        self._running = True
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())

        console.print("[bold green]✓ Muse streamer is running![/bold green]")
        console.print("[dim]Press Ctrl+C to stop...[/dim]\n")

        return True

    async def stop(self) -> None:
        """Stop the Muse streamer.

        This:
        1. Stops the keep-alive task
        2. Stops data streaming
        3. Disconnects from BLE
        4. Closes LSL outlets
        """
        if not self._running:
            return

        console.print("\n[cyan]Stopping Muse streamer...[/cyan]")

        # 1. Stop keep-alive task
        self._running = False
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass

        # 2 & 3. Stop streaming and disconnect
        await self.ble_client.disconnect()

        # 4. Close LSL streams
        self.lsl_streamer.close_streams()

        # Print statistics
        console.print("\n[bold]Packet Statistics:[/bold]")
        for sensor, count in self._packet_counts.items():
            console.print(f"  {sensor}: {count} packets")

        console.print("\n[green]✓ Muse streamer stopped[/green]")

    async def run_forever(self) -> None:
        """Start streaming and run until interrupted.

        This is a convenience method that starts the streamer and keeps
        it running until Ctrl+C is pressed.
        """
        if not await self.start():
            console.print("[red]Failed to start streamer[/red]")
            return

        try:
            # Run forever (or until Ctrl+C)
            while self._running:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        finally:
            await self.stop()

    def is_running(self) -> bool:
        """Check if the streamer is currently running.

        Returns:
            True if running, False otherwise
        """
        return self._running


# Standalone Test Function
async def test_streamer(device_address: str) -> None:
    """Test the custom Muse streamer.

    Args:
        device_address: MAC address of the Muse device
    """
    streamer = CustomMuseStreamer(device_address, muse_name=MUSE_NAME)
    await streamer.run_forever()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    device_address = os.getenv("DEVICE_MAC_ADDRESS")

    if not device_address:
        console.print("[red]Error: DEVICE_MAC_ADDRESS not set in .env[/red]")
        exit(1)

    asyncio.run(test_streamer(device_address))
