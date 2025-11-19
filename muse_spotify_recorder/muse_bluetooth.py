"""Muse Bluetooth LE client.

This module handles the BLE connection to the Muse headband, subscribes to sensor
characteristics, and provides callbacks for data notifications.
"""

import asyncio
from typing import Callable, Optional, Dict
from bleak import BleakClient, BleakScanner
from rich.console import Console

from .config import MUSE_NAME
from .muse_constants import (
    CONTROL_UUID,
    EEG_TP9_UUID,
    EEG_AF7_UUID,
    EEG_AF8_UUID,
    EEG_TP10_UUID,
    EEG_CHANNEL_UUIDS,
    ACCELEROMETER_UUID,
    GYROSCOPE_UUID,
)

console = Console()


# Control commands (based on muse-lsl protocol)
CMD_PRESET_P21 = bytes([0x04, 0x70, 0x32, 0x31, 0x0a])  # 'p21' - 4-channel EEG mode
CMD_START_STREAM = bytes([0x02, 0x64, 0x0a])  # 'd' - start streaming
CMD_STOP_STREAM = bytes([0x02, 0x68, 0x0a])  # 'h' - stop streaming
CMD_KEEP_ALIVE = bytes([0x02, 0x6b, 0x0a])  # 'k' - keep connection alive


class MuseBLEClient:
    """Manages BLE connection to Muse headband.

    This class handles:
    - Device discovery and connection
    - Subscribing to EEG, ACC, and GYRO characteristics
    - Sending control commands to start/stop streaming
    - Managing BLE notifications via callbacks
    """

    def __init__(self, device_address: str, muse_name: str = MUSE_NAME):
        """Initialize the Muse BLE client.

        Args:
            device_address: MAC address of the Muse device
            muse_name: Name of the Muse device (for display)
        """
        self.device_address = device_address
        self.muse_name = muse_name
        self.client: Optional[BleakClient] = None
        self._connected = False
        self._streaming = False

        # Callbacks for data notifications
        self.eeg_callbacks: Dict[str, Callable] = {}
        self.acc_callback: Optional[Callable] = None
        self.gyro_callback: Optional[Callable] = None

    async def connect(self, timeout: float = 30.0) -> bool:
        """Connect to the Muse device via BLE.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            console.print("[yellow]Already connected to Muse[/yellow]")
            return True

        console.print(f"[cyan]Scanning for {self.muse_name}...[/cyan]")

        # Find the device
        device = await BleakScanner.find_device_by_filter(
            lambda d, _: d.name == self.muse_name,
            timeout=timeout
        )

        if not device:
            console.print(f"[red]✗ {self.muse_name} not found![/red]")
            console.print("\nTroubleshooting:")
            console.print("  1. Make sure the Muse is powered ON")
            console.print("  2. Make sure the Muse is NOT connected to your phone")
            console.print("  3. Try power cycling the Muse")
            return False

        console.print(f"[green]✓ Found {self.muse_name} at {device.address}[/green]")
        console.print(f"[cyan]Connecting to Muse...[/cyan]")

        try:
            self.client = BleakClient(device, timeout=timeout)
            await self.client.connect()

            if not self.client.is_connected:
                console.print("[red]✗ Connection failed[/red]")
                return False

            self._connected = True
            console.print("[green]✓ Connected successfully![/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]✗ Connection error: {e}[/red]")
            return False

    async def subscribe_to_sensors(
        self,
        eeg_callbacks: Dict[str, Callable],
        acc_callback: Callable,
        gyro_callback: Callable
    ) -> bool:
        """Subscribe to all sensor characteristics.

        Args:
            eeg_callbacks: Dict mapping channel names to callback functions
                          e.g., {"TP9": callback_tp9, "AF7": callback_af7, ...}
            acc_callback: Callback for accelerometer notifications
            gyro_callback: Callback for gyroscope notifications

        Returns:
            True if all subscriptions successful, False otherwise

        Raises:
            RuntimeError: If not connected to device
        """
        if not self._connected or self.client is None:
            raise RuntimeError("Not connected to Muse. Call connect() first.")

        console.print("[cyan]Subscribing to sensors...[/cyan]")

        try:
            # Subscribe to EEG channels
            eeg_uuids = {
                "TP9": EEG_TP9_UUID,
                "AF7": EEG_AF7_UUID,
                "AF8": EEG_AF8_UUID,
                "TP10": EEG_TP10_UUID,
            }

            for channel_name, uuid in eeg_uuids.items():
                if channel_name in eeg_callbacks:
                    await self.client.start_notify(uuid, eeg_callbacks[channel_name])
                    self.eeg_callbacks[channel_name] = eeg_callbacks[channel_name]

            console.print(f"  ✓ Subscribed to {len(self.eeg_callbacks)} EEG channels")

            # Subscribe to accelerometer
            await self.client.start_notify(ACCELEROMETER_UUID, acc_callback)
            self.acc_callback = acc_callback
            console.print("  ✓ Subscribed to Accelerometer")

            # Subscribe to gyroscope
            await self.client.start_notify(GYROSCOPE_UUID, gyro_callback)
            self.gyro_callback = gyro_callback
            console.print("  ✓ Subscribed to Gyroscope")

            console.print("[green]✓ All sensors subscribed![/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]✗ Subscription error: {e}[/red]")
            return False

    async def start_streaming(self) -> bool:
        """Send control commands to start data streaming.

        This sends:
        1. Preset command (p21 - 4-channel EEG mode)
        2. Start stream command

        Returns:
            True if commands sent successfully, False otherwise

        Raises:
            RuntimeError: If not connected to device
        """
        if not self._connected or self.client is None:
            raise RuntimeError("Not connected to Muse. Call connect() first.")

        if self._streaming:
            console.print("[yellow]Streaming already started[/yellow]")
            return True

        console.print("[cyan]Starting Muse data stream...[/cyan]")

        try:
            # Send preset command (p21 - 4-channel EEG mode)
            console.print("  Sending preset command (p21)...")
            await self.client.write_gatt_char(CONTROL_UUID, CMD_PRESET_P21)
            await asyncio.sleep(0.5)

            # Send start stream command
            console.print("  Sending start stream command...")
            await self.client.write_gatt_char(CONTROL_UUID, CMD_START_STREAM)
            await asyncio.sleep(0.5)

            self._streaming = True
            console.print("[green]✓ Streaming started![/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]✗ Error starting stream: {e}[/red]")
            return False

    async def stop_streaming(self) -> bool:
        """Send control command to stop data streaming.

        Returns:
            True if command sent successfully, False otherwise

        Raises:
            RuntimeError: If not connected to device
        """
        if not self._connected or self.client is None:
            raise RuntimeError("Not connected to Muse. Call connect() first.")

        if not self._streaming:
            return True

        console.print("[cyan]Stopping Muse data stream...[/cyan]")

        try:
            await self.client.write_gatt_char(CONTROL_UUID, CMD_STOP_STREAM)
            await asyncio.sleep(0.5)

            self._streaming = False
            console.print("[green]✓ Streaming stopped[/green]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Error stopping stream: {e}[/red]")
            return False

    async def keep_alive(self) -> None:
        """Send keep-alive command to maintain connection.

        This should be called periodically (every few seconds) to prevent
        the Muse from disconnecting.
        """
        if self._connected and self.client is not None:
            try:
                await self.client.write_gatt_char(CONTROL_UUID, CMD_KEEP_ALIVE)
            except Exception:
                pass  # Silently ignore keep-alive errors

    async def disconnect(self) -> None:
        """Disconnect from the Muse and cleanup.

        This stops streaming, unsubscribes from all characteristics,
        and closes the BLE connection.
        """
        if not self._connected or self.client is None:
            return

        console.print("[cyan]Disconnecting from Muse...[/cyan]")

        try:
            # Stop streaming
            if self._streaming:
                await self.stop_streaming()

            # Unsubscribe from all characteristics
            eeg_uuids = {
                "TP9": EEG_TP9_UUID,
                "AF7": EEG_AF7_UUID,
                "AF8": EEG_AF8_UUID,
                "TP10": EEG_TP10_UUID,
            }

            for uuid in eeg_uuids.values():
                try:
                    await self.client.stop_notify(uuid)
                except Exception:
                    pass

            try:
                await self.client.stop_notify(ACCELEROMETER_UUID)
                await self.client.stop_notify(GYROSCOPE_UUID)
            except Exception:
                pass

            # Disconnect
            await self.client.disconnect()
            self._connected = False
            self._streaming = False

            console.print("[green]✓ Disconnected from Muse[/green]")

        except Exception as e:
            console.print(f"[red]✗ Disconnection error: {e}[/red]")

    def is_connected(self) -> bool:
        """Check if connected to the Muse.

        Returns:
            True if connected, False otherwise
        """
        return self._connected and self.client is not None and self.client.is_connected

    def is_streaming(self) -> bool:
        """Check if data streaming is active.

        Returns:
            True if streaming, False otherwise
        """
        return self._streaming
