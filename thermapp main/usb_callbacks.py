

import libusb as usb
import numpy as np
from constants import ThermappTransferStatus
from queue_handler import ThermappDataQueueHandler

class USBCallbacks:
    @usb.transfer_cb_fn
    def handle_usb_transfer_completion(transfer):
        """
        Callback function for USB transfer completion.

        Args:
            transfer (ctypes.Structure): USB transfer object.

        """
        if transfer.contents.status == ThermappTransferStatus.COMPLETED:
            received_data = np.array(transfer.contents.buffer[:transfer.contents.actual_length])
            ThermappDataQueueHandler.enqueue_received_data(received_data)
            usb.submit_transfer(transfer)