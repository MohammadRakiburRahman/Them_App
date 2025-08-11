import threading
import numpy as np
import cv2
import os
from detecconfig import cfg #############
from appconfig import ThermappConfig ###################
from inference import Inference
from constants import ThermappConstants
from data_processing import ThermappDataProcessing
from frame import FrameReader
from device import ThermappDevice
from transfer import AsyncTransferManager, TransferManager


class AnnotationApp:
    def __init__(self, device: ThermappDevice):
        self.device = device
        self.config = ThermappConfig().config_package
        self.transfer_manager = TransferManager(self.device, self.config)
        self.async_transfer_manager = AsyncTransferManager(self.transfer_manager)

        self.data_processing = ThermappDataProcessing()
        self.frame_reader = FrameReader()

        self.running = False

        self.calibration_image = np.zeros(ThermappConstants.PIXEL_DATA_SIZE, dtype=np.float32)
        self.global_offset = 70
        self.recalibration_frames_to_average = 50

        self.inference = Inference()
        self.class_map = {
            '0': 0,
            '1': 1,
            '2': 2
        }

        self.save_dir = "dataset/images/train"
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_interval = 30
        self.frame_counter = 0

    def start(self):
        thread_async_transfer = threading.Thread(target=self.async_transfer_manager.start_async_read)
        thread_async_transfer.start()

        self.initial_calibration()

        self.running = True
        thread_main_loop = threading.Thread(target=self.main_loop)
        thread_main_loop.start()

    def stop(self):
        self.async_transfer_manager.stop_async_read()
        self.running = False
        cv2.destroyAllWindows()

    def initial_calibration(self):
        sum_calibration = np.zeros((ThermappConstants.PIXEL_DATA_SIZE), dtype=np.float32)
        for i in range(self.recalibration_frames_to_average):
            frame = self.frame_reader.read_frame()
            if frame is not None:
                packet = self.data_processing.parse_frame_data(frame)
                sum_calibration += packet["pixels_data"]
        self.calibration_image = (sum_calibration / self.recalibration_frames_to_average).astype(np.float32)

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        frame_trans = (frame.astype(np.float32) - self.calibration_image) + self.global_offset
        frame_trans = np.clip(frame_trans, 0, 255).astype(np.uint8)
        return frame_trans

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

    def main_loop(self):
        while self.running:
            frame = self.frame_reader.read_frame()
            if frame is not None:
                try:
                    packet = self.data_processing.parse_frame_data(frame)
                    pixels_data = packet["pixels_data"]
                    
                    processed_frame = self.process_frame(pixels_data)
                    
                    img_reshaped = processed_frame.reshape((288, 384, 1))
                    img_rgb = np.repeat(img_reshaped, 3, axis=2)
                    img_rotated = cv2.rotate(img_rgb, cv2.ROTATE_90_CLOCKWISE)
                    
                    self.frame_counter += 1
                    
                    if self.frame_counter % self.save_interval == 0:
                        base_name = f"frame_{self.frame_counter}"
                        img_path = os.path.join(self.save_dir, f"{base_name}.jpg")
                        txt_path = os.path.join(self.save_dir, f"{base_name}.txt")
                        
                        cv2.imwrite(img_path, img_rotated)
                        self.generate_annotations_yolo(img_rotated, txt_path)
                    
                    # cv2.imshow("Thermal Camera", img_rotated)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
                    
                except Exception as e:
                    print(f"Error processing frame: {e}")


def main():
    try:
        device = ThermappDevice()
        app = AnnotationApp(device)
        app.start()
        
        while app.running:
            threading.Event().wait(1)
            
    except KeyboardInterrupt:
        app.stop()
    except Exception as e:
        print(f"Failed to start application: {e}")


if __name__ == "__main__":
    main()