

import ctypes as ct

class ConfigPackage(ct.Structure):
    """
    A structure representing the configuration package for the Thermapp device.
    """
    _fields_ = [
        ("none_volatile_data0", ct.c_uint),
        ("none_volatile_data1", ct.c_uint),
        ("modes", ct.c_ushort),
        ("none_volatile_dbyte0", ct.c_ushort),
        ("none_volatile_data2", ct.c_uint),
        ("none_volatile_data3", ct.c_uint),
        ("none_volatile_data4", ct.c_uint),
        ("none_volatile_data5", ct.c_uint),
        ("none_volatile_data6", ct.c_uint),
        ("VoutA", ct.c_ushort),
        ("none_volatile_data7", ct.c_ushort),
        ("VoutC", ct.c_ushort),
        ("VoutD", ct.c_ushort),
        ("VoutE", ct.c_ushort),
        ("none_volatile_data8", ct.c_ushort),
        ("none_volatile_data9", ct.c_uint),
        ("none_volatile_data10", ct.c_uint),
        ("none_volatile_data11", ct.c_uint),
        ("none_volatile_data12", ct.c_uint),
        ("none_volatile_data13", ct.c_uint),
    ]

class ThermappConfig:
    """
    A class to manage the configuration settings of the Thermapp device.

    Attributes:
        config_package (ConfigPackage): An instance of the ConfigPackage structure.
        default_values (dict): A dictionary of default values for the configuration fields.
    """

    def __init__(self):
        """
        Initializes a new instance of the ThermappConfig class and sets the default values.
        """
        self.config_package = ConfigPackage()
        self.default_values = {
            "none_volatile_data0": 0xa5a5a5a5,
            "none_volatile_data1": 0xa5d5a5a5,
            "modes": 0x0002,
            "none_volatile_dbyte0": 0x0000,
            "none_volatile_data2": 0x00000000,
            "none_volatile_data3": 0x01200000,
            "none_volatile_data4": 0x01200180,
            "none_volatile_data5": 0x00190180,
            "none_volatile_data6": 0x00000000,
            "VoutA": 0x0795,
            "none_volatile_data7": 0x0000,
            "VoutC": 0x058f,
            "VoutD": 0x08a2,
            "VoutE": 0x0b6d,
            "none_volatile_data8": 0x0b85,
            "none_volatile_data9": 0x00000000,
            "none_volatile_data10": 0x00400998,
            "none_volatile_data11": 0x00000000,
            "none_volatile_data12": 0x00000000,
            "none_volatile_data13": 0x0fff0000,
        }
        self.set_default_values()

    def set_default_values(self):
        """
        Sets the default values for the configuration fields in the config_package.
        """
        for field, value in self.default_values.items():
            setattr(self.config_package, field, value)

    def update_config_value(self, field: str, value):
        """
        Updates the value of a specific configuration field.

        Args:
            field (str): The name of the field to update.
            value: The new value to set for the field.

        Raises:
            AttributeError: If the field does not exist in the ConfigPackage.
        """
        if hasattr(self.config_package, field):
            setattr(self.config_package, field, value)
        else:
            raise AttributeError(f"ConfigPackage has no field named '{field}'")

    def get_config_value(self, field: str):
        """
        Retrieves the value of a specific configuration field.

        Args:
            field (str): The name of the field to retrieve.

        Returns:
            The value of the specified field.

        Raises:
            AttributeError: If the field does not exist in the ConfigPackage.
        """
        if hasattr(self.config_package, field):
            return getattr(self.config_package, field)
        else:
            raise AttributeError(f"ConfigPackage has no field named '{field}'")