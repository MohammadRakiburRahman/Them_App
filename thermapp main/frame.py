import threading
import numpy as np
import cv2
from constants import FrameHeaders, ThermappConstants
from queue_handler import ThermappDataQueueHandler
import time

# Planck conversion constants 
R1, B, F, O, R2 , E = 17711.559, 1447.2, 0.57999998, -4096, 0.025931966, 0.987  

def pixels_to_celsius(count: float) -> float:
    # Force to float32 so downstream math works
    c = np.float32(count)

    # **Subtract** the offset, then scale
    L = (c - O) * R2/E
    # avoid zero or negative arguments to log
    if L <= 0:
        L = 1e-3

    # invert Planck’s law
    T_k = B / np.log(R1 / L + F)
    T_k =  T_k + 25

    # to Celsius
    return float(T_k - 273.15) 

class FrameReader:
    """
    Reads and processes frames from a data queue.
    """
    
    def __init__(self):
        self.remaining_data = np.zeros((0), dtype=np.uint8)

    def read_frame(self) -> np.ndarray | None:
        data = self.remaining_data.copy()

        # Find and align the start header
        while True:
            data = self._ensure_data_length(data, ThermappConstants.PACKET_LENGTH)
            start_header_position = self._find_subarray_position(data, FrameHeaders.START)
            if start_header_position > -1:
                data = data[start_header_position:]
                break
            else:
                data = data[-len(FrameHeaders.START) + 1:]

        data = self._ensure_data_length(data, ThermappConstants.PACKET_LENGTH)

        if self._has_valid_end_header(data):
            self.remaining_data = np.zeros((0), dtype=np.uint8)
            return data.astype(np.uint8)
        else:
            self.remaining_data = data[len(FrameHeaders.START):]
            return None

    def _ensure_data_length(self, data: np.ndarray, required_length: int) -> np.ndarray:
        while len(data) < required_length:
            new_data = ThermappDataQueueHandler.read_data_from_queue(required_length - len(data))
            if new_data.size == 0:
                break
            data = np.append(data, new_data)
        return data

    def _find_subarray_position(self, array: np.ndarray, subarray: np.ndarray) -> int:
        subarray_length = len(subarray)
        for i in range(len(array) - subarray_length + 1):
            if (array[i:i + subarray_length] == subarray).all():
                return i
        return -1
    
    def _has_valid_end_header(self, data: np.ndarray) -> bool:
        return data.size >= len(FrameHeaders.END) and np.array_equal(data[-len(FrameHeaders.END):], FrameHeaders.END)


class DisplayThread:
    """
    Displays only the raw thermal frames in a window with FPS, basic stats,
    and live temperature overlay at the mouse cursor.
    """
    def __init__(self, resize_factor=2):
        # Frame queue and threading
        self.frame_queue = []
        self.lock = threading.Lock()
        self.running = True

        # Upscaling factor
        self.resize_factor = resize_factor

        # FPS tracking
        self.prev_time = None
        self.fps = 0.0

        # For mouse‐driven temperature overlay
        self.last_pixel_frame = None       # last_pixels holds the 8-bit, calibration+offset image
        self.temp_text = ''        # text to overlay
        self.text_pos = (10, 30)   # where to draw the text


        # Launch display thread
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE and self.last_pixel_frame is not None:
            h, w = self.last_pixel_frame.shape
            fx, fy = x // self.resize_factor, y // self.resize_factor
            if 0 <= fx < w and 0 <= fy < h:
                count = float(self.last_pixel_frame[fy, fx])
                temp_c =  pixels_to_celsius(count)
                self.temp_text = f"{temp_c:.1f}C"
                # offset the text so it doesn't cover the cursor
                self.text_pos = (x + 10, y - 10)

    def enqueue_frame(self, frame: np.ndarray):
        with self.lock:
            self.frame_queue.append(frame)

    def run(self):
        while self.running:
            frame = None
            with self.lock:
                if self.frame_queue:
                    frame = self.frame_queue.pop(0)
            if frame is not None:
                self.display_frame(frame)
            else:
                cv2.waitKey(1)

    def display_frame(self, calibrated_frame: np.ndarray):
        # 1) compute raw stats
        min_v = int(calibrated_frame.min())
        max_v = int(calibrated_frame.max())

        # 2) reshape to 2D
        h, w = 288, 384
        pixels_8bit = calibrated_frame.reshape((h, w)).astype(np.uint8)
        self.last_pixel_frame = pixels_8bit  # store for mouse callback

        # 3) prepare raw-BGR
        raw_bgr = cv2.cvtColor(pixels_8bit, cv2.COLOR_GRAY2BGR)

        # 4) upscale
        factor = self.resize_factor
        raw_res = cv2.resize(
            raw_bgr,
            (w * factor, h * factor),
            interpolation=cv2.INTER_NEAREST
        )

        # 5) compute FPS
        now = time.time()
        if self.prev_time is not None:
            dt = now - self.prev_time
            if dt > 0:
                self.fps = 1.0 / dt
        self.prev_time = now

        # 6) overlay resolution and stats
        overlay = f"Res: {w}x{h}  FPS: {self.fps:4.1f}  Min:{min_v}  Max:{max_v}"
        cv2.putText(raw_res, overlay, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # 7) overlay temperature at cursor
        if self.temp_text:
            cv2.putText(raw_res, self.temp_text, self.text_pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # 8) show
        cv2.imshow('Thermal Raw', raw_res)
        cv2.setMouseCallback('Thermal Raw', self._mouse_callback)
        cv2.waitKey(1)

    def stop(self):
        self.running = False
        self.thread.join()
        cv2.destroyWindow('Thermal Raw')
