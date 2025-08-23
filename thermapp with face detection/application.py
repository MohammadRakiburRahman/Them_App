import threading
import numpy as np
import cv2
import time
import os
from collections import deque
from config import ThermappConfig
from constants import ThermappConstants 
from data_processing import ThermappDataProcessing
from frame import FrameReader, DisplayThread
from device import ThermappDevice
from transfer import AsyncTransferManager, TransferManager
from inference import Inference


class ThermappApplication:
    

    def __init__(self, device: ThermappDevice):
        # Device and transfer setup
        self.device = device
        self.config = ThermappConfig().config_package
        self.transfer_manager = TransferManager(self.device, self.config)
        self.async_transfer_manager = AsyncTransferManager(self.transfer_manager)

        # Data processing and display
        self.data_processing = ThermappDataProcessing()
        self.frame_reader = FrameReader()
        self.display_thread = DisplayThread()
        
        self.inference = Inference()

        self.class_map = {
            '0': 0,
            '1': 1,
            '2': 2
        }

        # Control flags
        self.running = True

        # Circular buffer for recalibration
        self.circular_buffer_size = 300
        self.circular_buffer = deque(maxlen=self.circular_buffer_size)

        # Timing and calibration parameters
        self.start_time = time.time()
        self.warmup_duration = 300  # 5 minutes
        self.recalibration_frames_to_average = 50
        self.recalibration_interval_fast = 30   # seconds during warmup
        self.recalibration_interval_slow = 300  # seconds after warmup
        self.last_recalibration_time = self.start_time

        # Calibration & offset
        self.calibration_image = np.zeros(ThermappConstants.PIXEL_DATA_SIZE, dtype=np.float32)
        self.global_offset = 70  # initial brightness offset

        # Dataset saving configuration
        self.save_dir = "dataset"
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_interval = 5       # save every 5 frames
        self.frame_counter = 0        # initialize frame counter
        self.plotted_raw = True  # added for raw data plot

        
       

    def start(self):
        print("[DEBUG] Starting async transfer thread")
        thread_async_transfer = threading.Thread(target=self.async_transfer_manager.start_async_read)
        thread_async_transfer.start()

        print("[DEBUG] Performing initial calibration")
        self.initial_calibration()

        


        print("[DEBUG] Starting main loop thread")
        self.running = True
        thread_main_loop = threading.Thread(target=self.main_loop)
        thread_main_loop.start()

    def stop(self):
        self.async_transfer_manager.stop_async_read()
        self.running = False
        self.display_thread.stop()
        cv2.destroyAllWindows()

    def initial_calibration(self):
        sum_calibration = np.zeros((ThermappConstants.PIXEL_DATA_SIZE), dtype=np.float32)
        for i in range(self.recalibration_frames_to_average):
            frame = self.frame_reader.read_frame()
            print(f"[DEBUG] Initial calibration frame {i+1}/{self.recalibration_frames_to_average}")
            if frame is not None:
                packet = self.data_processing.parse_frame_data(frame)
                sum_calibration += packet["pixels_data"]
        self.calibration_image = (sum_calibration / self.recalibration_frames_to_average).astype(np.float32)
        print("[DEBUG] Initial calibration complete.")

    def main_loop(self):
        print("[DEBUG] Main loop started")
        while self.running:
            frame = self.frame_reader.read_frame()
            if frame is not None:
                try:
                    # Parse raw data
                    packet = self.data_processing.parse_frame_data(frame)
                   # print("Raw pixel values:", packet["pixels_data"]) ########### uncomment to print the raw values from camera input

                    pixels_data = packet["pixels_data"]
                    self.circular_buffer.append(pixels_data)

                    # Process and display
                    processed_frame = self.process_frame(pixels_data)
                    self.display_thread.enqueue_frame(processed_frame)

                    # Save frame for dataset every Nth frame
                    self.frame_counter += 1
                    if self.frame_counter % self.save_interval == 0:
                        save_path = os.path.join(self.save_dir,
                                                f"frame_predicted_{self.frame_counter}.jpg")

                        # RGB conversion / resize / rotate steps …
                        img_reshaped = processed_frame.reshape((288, 384, 1))
                        img_rgb      = np.repeat(img_reshaped, 3, axis=2)
                        img_resized  = cv2.resize(img_rgb, (384*2, 288*2))
                        # img_rotated  = cv2.rotate(img_resized, cv2.ROTATE_90_CLOCKWISE)

                        # frame_out, boxes, _, class_ids = self.inference.infer(img_resized)

                        base_name = f"frame_{self.frame_counter}"
                        img_path = os.path.join(self.save_dir, f"{base_name}.jpg")
                        txt_path = os.path.join(self.save_dir, f"{base_name}.txt")

                        cv2.imwrite(img_path, img_resized)
                        frame_out_, boxes_, class_ids_ = self.generate_annotations_yolo(img_resized, txt_path)

                        # write out the predicted face images
                        # cv2.imwrite(save_path, frame_out_)

                        #rollign recalibration 
                        #self.check_recalibration() #uncomment it o apply rolling recalibration

                except Exception as e:
                    print(f"Error processing frame: {e}")

    def generate_annotations_yolo(self, img, txt_path):
        w_img = img.shape[1]
        h_img = img.shape[0]
        
        frame_out, boxes, _, class_ids = self.inference.infer(img)
        
        with open(txt_path, 'w') as textfile:
            for i, box in enumerate(boxes):
                class_id = int(class_ids[i])
                
                if str(class_id) in self.class_map:
                    mapped_class_id = self.class_map[str(class_id)]
                    
                    w = box[2]
                    h = box[3]
                    x = box[0]
                    y = box[1]
                    
                    textfile.write(f'{mapped_class_id} {(x + w / 2) / w_img} {(y + h / 2) / h_img} {w / w_img} {h / h_img}\n')
        
        return frame_out, boxes, class_ids

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies calibration and global offset to raw frame data.
        """
        frame_trans = (frame.astype(np.float32) - self.calibration_image) + self.global_offset
        frame_trans = np.clip(frame_trans, 0, 255).astype(np.uint8)
        print(f"[DEBUG] Displaying frame | min: {frame_trans.min()} max: {frame_trans.max()}")
        return frame_trans

    def check_recalibration(self):
        """
        Periodically re-calibrates using the circular buffer of recent frames.
        """
        current_time = time.time()
        elapsed = current_time - self.start_time
        # choose interval based on warmup
        interval = (self.recalibration_interval_fast
                    if elapsed < self.warmup_duration
                    else self.recalibration_interval_slow)

        if (current_time - self.last_recalibration_time >= interval and
                len(self.circular_buffer) >= self.recalibration_frames_to_average):
            self.last_recalibration_time = current_time
            print("[DEBUG] Performing recalibration from circular buffer...")
            frames = list(self.circular_buffer)[-self.recalibration_frames_to_average:]
            stacked = np.stack(frames)
            average_calibration = np.mean(stacked, axis=0).astype(np.float32)
            self.apply_blended_calibration(average_calibration)
            self.auto_adjust_global_offset()
            print("[DEBUG] Recalibration applied.")

    def apply_blended_calibration(self, new_calibration: np.ndarray):
        self.calibration_image = 0.9 * self.calibration_image + 0.1 * new_calibration

    def auto_adjust_global_offset(self):
        """
        Adjusts global offset to center image brightness around mid-range.
        """
        test_frame = (list(self.circular_buffer)[-1].astype(np.float32)
                      - self.calibration_image)
        mean_value = np.mean(test_frame)
        desired_mean = 128
        offset_adjustment = desired_mean - mean_value
        self.global_offset += 0.5 * offset_adjustment
        self.global_offset = np.clip(self.global_offset, 50, 150)
        print(f"[DEBUG] Adjusted global offset to: {self.global_offset}")