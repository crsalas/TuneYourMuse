"""Muse 2 BLE GATT constants and UUIDs.

This module contains all the Bluetooth Low Energy GATT service and characteristic
UUIDs discovered from the Muse-DC0F headband. These UUIDs are used by the custom
bleak-based Muse streamer implementation.

All UUIDs were verified by connecting to Muse-DC0F and enumerating services
using the discover_muse_characteristics.py script.
"""

# GATT Service UUIDs
# Main Muse service (Interaxon Inc.)
MUSE_SERVICE_UUID = "0000fe8d-0000-1000-8000-00805f9b34fb"



# EEG Characteristic UUIDs
# 4 EEG channels: TP9, AF7, AF8, TP10
# Each characteristic streams one channel of EEG data
# Properties: NOTIFY (push notifications when data is available)
# Sample rate: 256 Hz per channel

EEG_TP9_UUID = "273e0003-4c4d-454d-96be-f03bac821358"  # Left ear (temporal-parietal)
EEG_AF7_UUID = "273e0004-4c4d-454d-96be-f03bac821358"  # Left forehead (frontal)
EEG_AF8_UUID = "273e0005-4c4d-454d-96be-f03bac821358"  # Right forehead (frontal)
EEG_TP10_UUID = "273e0006-4c4d-454d-96be-f03bac821358"  # Right ear (temporal-parietal)

# List of all EEG channel UUIDs in order
EEG_CHANNEL_UUIDS = [
    EEG_TP9_UUID,
    EEG_AF7_UUID,
    EEG_AF8_UUID,
    EEG_TP10_UUID,
]

# Channel names corresponding to EEG_CHANNEL_UUIDS
EEG_CHANNEL_NAMES = ["TP9", "AF7", "AF8", "TP10"]


# Accelerometer Characteristic UUID
# 3-axis accelerometer (X, Y, Z)
# Properties: NOTIFY
# Sample rate: ~52 Hz
# Units: g (gravitational acceleration)

ACCELEROMETER_UUID = "273e000a-4c4d-454d-96be-f03bac821358"


# Gyroscope Characteristic UUID
# 3-axis gyroscope (X, Y, Z)
# Properties: NOTIFY
# Sample rate: ~52 Hz
# Units: deg/s (degrees per second)

GYROSCOPE_UUID = "273e0009-4c4d-454d-96be-f03bac821358"


# Other Discovered Characteristics (for reference)
# These characteristics were discovered but their exact purpose is unknown.
# They are not currently used in the streamer implementation.

CONTROL_UUID = "273e0001-4c4d-454d-96be-f03bac821358"  # Write + Notify
UNKNOWN_0002_UUID = "273e0002-4c4d-454d-96be-f03bac821358"  # Notify
UNKNOWN_0007_UUID = "273e0007-4c4d-454d-96be-f03bac821358"  # Notify
UNKNOWN_0008_UUID = "273e0008-4c4d-454d-96be-f03bac821358"  # Notify
UNKNOWN_000B_UUID = "273e000b-4c4d-454d-96be-f03bac821358"  # Notify


# PPG Characteristic UUIDs (NOT PRESENT on Muse-DC0F)
# These PPG (photoplethysmography) UUIDs are documented in Muse SDK but are
# NOT present on the Muse-DC0F device. Attempting to subscribe to them causes
# BleakCharacteristicNotFoundError.

# PPG_0_UUID = "273e000e-4c4d-454d-96be-f03bac821358"  # NOT PRESENT
# PPG_1_UUID = "273e000f-4c4d-454d-96be-f03bac821358"  # NOT PRESENT
# PPG_2_UUID = "273e0010-4c4d-454d-96be-f03bac821358"  # NOT PRESENT


# Data Format Constants
# EEG data format
# Muse sends EEG data in packets containing multiple 12-bit samples
# The exact packet format needs to be determined by examining raw data

EEG_SAMPLE_RATE = 256  # Hz
EEG_CHANNEL_COUNT = 4

# Accelerometer and Gyroscope data format
# Typically sent as 3 int16 values (X, Y, Z) in little-endian format

ACC_SAMPLE_RATE = 52  # Hz (approximate)
ACC_CHANNEL_COUNT = 3

GYRO_SAMPLE_RATE = 52  # Hz (approximate)
GYRO_CHANNEL_COUNT = 3


# LSL Stream Configuration
# Stream names for Lab Streaming Layer outlets
LSL_EEG_NAME = "Muse-EEG"
LSL_EEG_TYPE = "EEG"

LSL_ACC_NAME = "Muse-ACC"
LSL_ACC_TYPE = "ACC"

LSL_GYRO_NAME = "Muse-GYRO"
LSL_GYRO_TYPE = "GYRO"