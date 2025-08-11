

import libusb as usb
import ctypes as ct

class ThermappDevice:
    """
    Class representing a Thermapp device.

    Attributes:
        vendor_id (int): USB vendor ID of the device.
        product_id (int): USB product ID of the device.
        handler (ctypes.POINTER): Handler for the USB device.
    """
    
    def __init__(self, vendor_id=0x1772, product_id=2):
        """
        Initializes the ThermappDevice with the given vendor and product IDs.

        Args:
            vendor_id (int): USB vendor ID of the device. Defaults to 0x1772.
            product_id (int): USB product ID of the device. Defaults to 2.
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.handler = None

    def open(self):
        """
        Opens the USB device, claims the interface, and configures the device.

        Raises:
            IOError: If there is an I/O error.
            usb.USBError: If there is a USB error.
            Exception: If any other unexpected error occurs.
        """
        try:
            self.handler = self._open_device()
            self._claim_interface()
            self._perform_control_transfers()
        except IOError as io_error:
            print(f"I/O error: {io_error}")
            self.close()
            raise
        except usb.USBError as usb_error:
            print(f"USB error: {usb_error}")
            self.close()
            raise
        except Exception as error:
            print(f"Unexpected error: {error}, {type(error)}")
            self.close()
            raise

    def close(self):
        """
        Releases the claimed interface and closes the USB device.
        """
        if self.handler:
            usb.release_interface(self.handler, 0)
            usb.close(self.handler)
            self.handler = None

    def _open_device(self):
        """
        Opens the USB device with the specified vendor and product IDs.

        Returns:
            ctypes.POINTER: Pointer to the opened USB device.

        Raises:
            IOError: If the device cannot be found.
        """
        device_pointer = usb.open_device_with_vid_pid(None, self.vendor_id, self.product_id)
        if not device_pointer:
            raise IOError(f"Unable to find USB device with Vendor ID {self.vendor_id} and Product ID {self.product_id}.")
        return device_pointer.contents

    def _claim_interface(self):
        """
        Claims the interface of the opened USB device.

        Raises:
            IOError: If claiming the interface fails.
        """
        status = usb.claim_interface(self.handler, 0)
        if status != usb.LIBUSB_SUCCESS:
            raise IOError(f"Claim interface failed: {usb.error_name(status)}.")

    def _perform_control_transfers(self):
        """
        Configures the USB device by performing a series of control transfers.
        """
        buffer = (ct.c_ubyte * 255)()
        control_transfers = self._get_control_transfers()

        for direction, request, value, index, length in control_transfers:
            self._perform_control_transfer(direction, request, value, index, buffer, length)

    def _get_control_transfers(self):
        """
        Returns a list of control transfer parameters for device configuration.

        Returns:
            list: A list of tuples containing control transfer parameters.
        """
        return [
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0100, 0x0000, 0x12),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0200, 0x0000, 0x09),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0200, 0x0000, 0x20),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0300, 0x0000, 0xff),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0302, 0x0409, 0xff),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0301, 0x0409, 0xff),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0303, 0x0409, 0xff),
            (usb.LIBUSB_TRANSFER_TYPE_CONTROL, 0x09, 0x0001, 0x0000, 0x00),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0304, 0x0409, 0xff),
            (usb.LIBUSB_ENDPOINT_IN, 0x06, 0x0305, 0x0409, 0xff)
        ]

    def _perform_control_transfer(self, direction, request, value, index, buffer, length):
        """
        Performs a control transfer to the USB device.

        Args:
            direction (int): Direction of the transfer.
            request (int): Request type.
            value (int): Value parameter.
            index (int): Index parameter.
            buffer (ctypes array): Data buffer.
            length (int): Length of the data to transfer.

        Raises:
            IOError: If the control transfer fails.
        """
        status = usb.control_transfer(self.handler, direction, request, value, index, buffer, length, 0)
        if status < 0:
            raise IOError(f"Control transfer failed with status {status}: {usb.error_name(status)}.")