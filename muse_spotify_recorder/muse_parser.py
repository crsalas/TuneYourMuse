"""Muse 2 data packet parser.

This module contains functions to parse raw BLE GATT notification packets from
the Muse 2 headband and convert them to calibrated physical units.

Packet formats are based on the muse-lsl implementation:
https://github.com/alexandrebarachant/muse-lsl

EEG data: 12-bit samples packed into bytes, converted to microvolts (µV)
Accelerometer data: int16 samples, converted to g (gravitational acceleration)
Gyroscope data: int16 samples, converted to deg/s (degrees per second)
"""

import struct
from typing import Tuple, List
import numpy as np
import bitstring


# Constants (from muse-lsl)
# EEG conversion factor: maps 12-bit range (0-4095) centered at 2048 to µV
EEG_SCALE_FACTOR = 0.48828125  # microvolts per unit

# Accelerometer conversion factor: converts int16 to g (gravitational acceleration)
ACC_SCALE_FACTOR = 0.0000610352  # g per unit

# Gyroscope conversion factor: converts int16 to deg/s
GYRO_SCALE_FACTOR = 0.0074768  # degrees/second per unit


# EEG Packet Parsing
def parse_eeg_packet(data: bytes) -> Tuple[int, np.ndarray]:
    """Parse a Muse EEG packet.

    Muse EEG packets contain:
    - 1× uint16: packet index (sequence number)
    - 12× uint12: EEG samples (12-bit values packed)

    Total: 2 + 18 = 20 bytes

    Args:
        data: Raw packet bytes (should be 20 bytes)

    Returns:
        Tuple of (packet_index, samples) where:
        - packet_index: uint16 sequence number
        - samples: numpy array of 12 float values in microvolts (µV)

    Raises:
        ValueError: If packet size is not 20 bytes
    """
    if len(data) != 20:
        raise ValueError(f"EEG packet must be 20 bytes, got {len(data)}")

    # Use bitstring to unpack the packed 12-bit samples
    bits = bitstring.Bits(bytes=data)
    pattern = "uint:16," + "uint:12," * 12
    unpacked = bits.unpack(pattern)

    packet_index = unpacked[0]
    raw_samples = np.array(unpacked[1:], dtype=np.float64)

    # Convert 12-bit values (0-4095, centered at 2048) to microvolts
    samples_uv = EEG_SCALE_FACTOR * (raw_samples - 2048)

    return packet_index, samples_uv

# Accelerometer Packet Parsing
def parse_acc_packet(data: bytes) -> Tuple[int, np.ndarray]:
    """Parse a Muse accelerometer packet.

    Accelerometer packets contain:
    - 1× uint16: packet index
    - 9× int16: 3 samples × 3 axes (X, Y, Z) in column-major order

    Total: 2 + 18 = 20 bytes

    The data is organized as:
    [index, x1, y1, z1, x2, y2, z2, x3, y3, z3]

    Args:
        data: Raw packet bytes (should be 20 bytes)

    Returns:
        Tuple of (packet_index, samples) where:
        - packet_index: uint16 sequence number
        - samples: numpy array of shape (3, 3) with values in g units
          Each row is one sample: [x, y, z]

    Raises:
        ValueError: If packet size is not 20 bytes
    """
    if len(data) != 20:
        raise ValueError(f"Accelerometer packet must be 20 bytes, got {len(data)}")

    # Unpack using bitstring
    bits = bitstring.Bits(bytes=data)
    pattern = "uint:16," + "int:16," * 9
    unpacked = bits.unpack(pattern)

    packet_index = unpacked[0]
    raw_data = np.array(unpacked[1:], dtype=np.float64)

    # Reshape from column-major (Fortran order) to (3 samples, 3 axes)
    samples = raw_data.reshape((3, 3), order='F')

    # Convert to g units
    samples_g = samples * ACC_SCALE_FACTOR

    return packet_index, samples_g


# Gyroscope Packet Parsing
def parse_gyro_packet(data: bytes) -> Tuple[int, np.ndarray]:
    """Parse a Muse gyroscope packet.

    Gyroscope packets have the same structure as accelerometer packets:
    - 1× uint16: packet index
    - 9× int16: 3 samples × 3 axes (X, Y, Z) in column-major order

    Total: 2 + 18 = 20 bytes

    Args:
        data: Raw packet bytes (should be 20 bytes)

    Returns:
        Tuple of (packet_index, samples) where:
        - packet_index: uint16 sequence number
        - samples: numpy array of shape (3, 3) with values in deg/s
          Each row is one sample: [x, y, z]

    Raises:
        ValueError: If packet size is not 20 bytes
    """
    if len(data) != 20:
        raise ValueError(f"Gyroscope packet must be 20 bytes, got {len(data)}")

    # Unpack using bitstring
    bits = bitstring.Bits(bytes=data)
    pattern = "uint:16," + "int:16," * 9
    unpacked = bits.unpack(pattern)

    packet_index = unpacked[0]
    raw_data = np.array(unpacked[1:], dtype=np.float64)

    # Reshape from column-major (Fortran order) to (3 samples, 3 axes)
    samples = raw_data.reshape((3, 3), order='F')

    # Convert to degrees/second
    samples_dps = samples * GYRO_SCALE_FACTOR

    return packet_index, samples_dps


# Convenience Functions
def parse_eeg_samples_only(data: bytes) -> np.ndarray:
    """Parse EEG packet and return only the samples (no packet index).

    Args:
        data: Raw packet bytes

    Returns:
        numpy array of 12 float values in microvolts (µV)
    """
    _, samples = parse_eeg_packet(data)
    return samples


def parse_acc_samples_only(data: bytes) -> np.ndarray:
    """Parse accelerometer packet and return only the samples (no packet index).

    Args:
        data: Raw packet bytes

    Returns:
        numpy array of shape (3, 3) with values in g units
    """
    _, samples = parse_acc_packet(data)
    return samples


def parse_gyro_samples_only(data: bytes) -> np.ndarray:
    """Parse gyroscope packet and return only the samples (no packet index).

    Args:
        data: Raw packet bytes

    Returns:
        numpy array of shape (3, 3) with values in deg/s
    """
    _, samples = parse_gyro_packet(data)
    return samples
