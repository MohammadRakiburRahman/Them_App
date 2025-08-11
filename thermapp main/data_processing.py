
import numpy as np

from constants import ThermappConstants
from collections import namedtuple
from typing import Union, Dict

class ThermappDataProcessing:
    """
    A class to handle the data processing for the Thermapp device.
    """
    FieldSpec = namedtuple("FieldSpec", ["name", "length", "dtype"])

    def __init__(self):
        """
        Initializes the ThermappDataProcessing class with the frame fields specification.
        """
        self.frame_fields = [
            self.FieldSpec("Start_Header", 4, int),
            self.FieldSpec("some_data0", 2, int),
            self.FieldSpec("id", 4, int),
            self.FieldSpec("some_data1", 16, int),
            self.FieldSpec("temperature", 2, int),
            self.FieldSpec("some_data2", 20, int),
            self.FieldSpec("frame_number", 2, int),
            self.FieldSpec("some_data3", 10, int),
            self.FieldSpec("pixels_data", ThermappConstants.PIXEL_DATA_SIZE * 2, np.ndarray),
            self.FieldSpec("some_data4", 448, int),
            self.FieldSpec("End_Header", 4, int)
        ]

    @staticmethod
    def bytes_to_int(data: bytes) -> int:
        """
        Converts a byte array to an integer.

        Args:
            data (bytes): The byte array to convert.

        Returns:
            int: The integer representation of the byte array.
        """
        return int.from_bytes(data[::-1], "big")

    @staticmethod
    def bytes_to_uint16_list(data: bytes) -> np.ndarray:
        """
        Converts a byte array to a list of unsigned 16-bit integers.

        Args:
            data (bytes): The byte array to convert.

        Returns:
            np.ndarray: The array of 16-bit unsigned integers.
        """
        return np.frombuffer(data, dtype=np.uint16)

    def parse_frame_data(self, data: bytes) -> Dict[str, Union[int, np.ndarray, None]]:
        """
        Extracts and processes received frame data according to the frame fields specification.

        Args:
            data (bytes): The raw data received.

        Returns:
            dict: A dictionary containing the processed fields from the data.
        """
        expected_length = sum(field.length for field in self.frame_fields)
        if len(data) != expected_length:
            raise ValueError(f"Input data length ({len(data)}) does not match the expected frame length ({expected_length})")

        result = {}
        idx = 0

        for field_name, field_length, field_dtype in self.frame_fields:
            field_data = data[idx:idx + field_length]
            result[field_name] = self.parse_field_data(field_data, field_dtype)
            idx += field_length

        return result

    def parse_field_data(self, field_data: bytes, field_dtype) -> Union[int, np.ndarray, None]:
        """
        Parses the raw data for a single field based on its type.

        Args:
            field_data (bytes): The raw data for the field.
            field_dtype (type): The data type of the field.

        Returns:
            int or np.ndarray: The parsed data.
        """
        
        try:
            if field_dtype == np.ndarray:
                return self.bytes_to_uint16_list(field_data)
            else:
                return self.bytes_to_int(field_data)
        except ValueError as e:
            raise ValueError(f"Error parsing field data: {e}")