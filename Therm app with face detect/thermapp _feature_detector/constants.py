

import numpy as np

class ThermappStatus:
    """
    Enumeration of possible Thermapp device statuses.
    
    Attributes:
        INACTIVE (int): The device is inactive.
        RUNNING (int): The device is running.
        CANCELING (int): The device is canceling operations.
    """
    INACTIVE = 0
    RUNNING = 2
    CANCELING = 1

class ThermappEndpoint:
    """
    Enumeration of USB endpoint directions for Thermapp device.
    
    Attributes:
        OUT (int): USB endpoint direction for outgoing data.
        IN (int): USB endpoint direction for incoming data.
    """
    OUT = 0x00
    IN = 0x80

class ThermappTransferStatus:
    """
    Enumeration of possible statuses for USB transfers.
    
    Attributes:
        COMPLETED (int): The transfer has completed successfully.
    """
    COMPLETED = 0

class FrameHeaders:
    """
    Constants representing the start and end headers of a frame.
    
    Attributes:
        START (np.ndarray): Start header for a frame.
        END (np.ndarray): End header for a frame.
    """
    START = np.array([0xA5, 0xA5, 0xD5, 0xA5], dtype=np.uint8)
    END = np.array([0xA5, 0xA5, 0xA5, 0xA5], dtype=np.uint8)

class ThermappConstants:
    """
    Constants used in Thermapp device operations.
    
    Attributes:
        PACKET_SIZE (int): Size of a data packet.
        PACKET_LENGTH (int): Length of a data packet.
        DEFAULT_BUFFER_LENGTH (int): Default length of data buffers.
        PIXEL_DATA_SIZE (int): Size of the pixel data array.
        BULK_TIMEOUT (int): Timeout for bulk transfers.
        DEFAULT_BUFFER_COUNT (int): Number of default buffers.
        DEFAULT_BUFFER_REMAIN (int): Remaining size after dividing packet size by buffer length.
    """
    PACKET_SIZE = 221688
    PACKET_LENGTH = 221696
    DEFAULT_BUFFER_LENGTH = 16384
    PIXEL_DATA_SIZE = 384 * 288
    BULK_TIMEOUT = 0

    DEFAULT_BUFFER_COUNT = PACKET_SIZE // DEFAULT_BUFFER_LENGTH
    DEFAULT_BUFFER_REMAIN = PACKET_SIZE % DEFAULT_BUFFER_LENGTH
