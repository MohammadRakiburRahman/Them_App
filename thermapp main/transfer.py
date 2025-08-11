
import libusb as usb
import ctypes as ct

from constants import ThermappConstants, ThermappEndpoint, ThermappStatus
from usb_callbacks import USBCallbacks

class TransferManager:
    """
    Manages USB transfers for a Thermapp device.
    """

    def __init__(self, device, config):
        self.device = device
        self.config = config
        self.outgoing_transfer = None
        self.incoming_transfers = []
        self.incoming_buffers = []
    
    def allocate_outgoing_transfer(self):
        self.outgoing_transfer = usb.alloc_transfer(0)
        if self.outgoing_transfer is None:
            raise OSError("Cannot allocate space for outgoing_transfer")

        usb.fill_bulk_transfer(
            self.outgoing_transfer,
            self.device.handler,
            ThermappEndpoint.OUT | 2,
            ct.cast(ct.addressof(self.config), ct.POINTER(ct.c_ubyte)),
            64,
            TransferManager.outgoing_transfer_callback,
            None,
            -1
        )
        usb.submit_transfer(self.outgoing_transfer)
    
    def allocate_async_buffers(self):
        buffer_count = ThermappConstants.DEFAULT_BUFFER_COUNT + int(ThermappConstants.DEFAULT_BUFFER_REMAIN != 0)
        buffer_size = ThermappConstants.DEFAULT_BUFFER_LENGTH * ct.sizeof(ct.c_ubyte)

        self.incoming_transfers = [usb.alloc_transfer(0) for _ in range(buffer_count)]
        self.incoming_buffers = [ct.create_string_buffer(buffer_size) for _ in range(buffer_count)]
    
    @usb.transfer_cb_fn
    def outgoing_transfer_callback(transfer):
        pass
            
class AsyncTransferManager:
    """
    Manages asynchronous USB transfers.
    """
    def __init__(self, transfer_manager):
        self.transfer_manager = transfer_manager
        self.async_status = ThermappStatus.INACTIVE
    
    def stop_async_read(self):
        """
        Stops asynchronous USB transfers.
        """
        if self.async_status == ThermappStatus.INACTIVE:
            return  # If already stopped, do nothing

        self.async_status = ThermappStatus.CANCELING
        
        # Cancel all incoming transfers
        for transfer in self.transfer_manager.incoming_transfers:
            if transfer:
                usb.cancel_transfer(transfer)

        # Clean up resources
        self.transfer_manager.incoming_transfers.clear()
        self.transfer_manager.incoming_buffers.clear()

        # Reset async status
        self.async_status = ThermappStatus.INACTIVE

    def start_async_read(self):
        self.transfer_manager.incoming_transfers = []
        self.transfer_manager.incoming_buffers = []

        if self.async_status != ThermappStatus.INACTIVE:
            return -2

        self.async_status = ThermappStatus.RUNNING
        self.transfer_manager.allocate_outgoing_transfer()
        self.transfer_manager.allocate_async_buffers()

        for i in range(ThermappConstants.DEFAULT_BUFFER_COUNT + int(ThermappConstants.DEFAULT_BUFFER_REMAIN != 0)):
            usb.fill_bulk_transfer(
                self.transfer_manager.incoming_transfers[i],
                self.transfer_manager.device.handler,
                ThermappEndpoint.IN | 1,
                ct.cast(ct.pointer(self.transfer_manager.incoming_buffers[i]), ct.POINTER(ct.c_ubyte)),
                ThermappConstants.DEFAULT_BUFFER_LENGTH,
                USBCallbacks.handle_usb_transfer_completion,
                None,
                ThermappConstants.BULK_TIMEOUT
            )
            if usb.submit_transfer(self.transfer_manager.incoming_transfers[i]) < 0:
                self.async_status = ThermappStatus.CANCELING
                break

        tv = usb.timeval(1, 0)
        while self.async_status != ThermappStatus.INACTIVE:
            usb.handle_events_timeout_completed(None, ct.byref(tv), None)