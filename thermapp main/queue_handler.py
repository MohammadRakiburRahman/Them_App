

from multiprocessing import Queue
import queue
import numpy as np

class ThermappDataQueueHandler:
    """
    Handles the data queue for received Thermapp data.

    Attributes:
        received_data_queue (queue.Queue): A queue to store received Thermapp data.
    """
    remaining_data = np.zeros((0), dtype=np.uint8)
        
    received_data_queue = Queue()

    @staticmethod
    def enqueue_received_data(data_array: np.ndarray) -> None:
        """
        Adds data to the received data queue.

        Args:
            data_array (np.ndarray): The data to be added to the queue.

        Raises:
            ValueError: If the data is not a numpy ndarray.
        """
        if not isinstance(data_array, np.ndarray):
            raise ValueError("Data must be a numpy ndarray.")
        try:
            ThermappDataQueueHandler.received_data_queue.put(data_array, block= True)

        except queue.Full:
            print("Warning: The queue is full. Data was not added.")
    
    
    def read_data_from_queue(item_count: int) -> np.ndarray:
        """
        Reads the specified number of items from the data queue.

        Args:
            item_count (int): The number of items to read from the queue.

        Returns:
            np.ndarray: The read data.
        """
        read_data = np.append(ThermappDataQueueHandler.remaining_data, np.zeros(0))
        try:
            while len(read_data) < item_count:
                read_data = np.append(read_data, ThermappDataQueueHandler.received_data_queue.get())
        except queue.Empty:
            return read_data
        ThermappDataQueueHandler.remaining_data = read_data[item_count:]
        return read_data[:item_count]