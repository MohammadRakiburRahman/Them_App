from ultralytics import YOLO
from detecconfig import cfg #############
#import cfg
import cv2
import yaml
import os


class Inference:
    def __init__(self):
        self.model = YOLO(cfg.detector.weight_file)
        self.names = self.model.names
        self.COLORS = cfg.general.COLORS

    def infer(self, frame):
        # Run the model
        processed_boxes = []
        processed_confidence = []
        processed_class_id = []
        names = []
        results = self.model.predict(task= 'detect',
                                     source=frame, conf=cfg.detector.OBJECTNESS_CONFIDANCE,
                                     iou=cfg.detector.NMS_THRESHOLD,
                                     classes=cfg.detector.classes,
                                     device=cfg.detector.device,
                                     verbose=cfg.detector.verbose)
        for result in results:
            boxes = result.boxes.xywh.tolist()  # box with xywh format, (N, 4)
            class_ids = result.boxes.cls.tolist()  # cls, (N, 1)
            confidences = result.boxes.conf.tolist()  # confidence score, (N, 1)

            for i, box in enumerate(boxes):
                class_id = int(class_ids[i])
                names.append(self.names[class_id])
                confidence = confidences[i]
                w = box[2]
                h = box[3]
                x = box[0] - w / 2
                y = box[1] - h / 2
                p1, p2 = (int(x), int(y)), (int(x + w), int(y + h))
                line_width = 2 or max(round(sum(frame.shape) / 2 * 0.003), 2)  # line width
                color = self.COLORS[list(self.COLORS)[int(class_id) % len(self.COLORS)]]
                if cfg.flags.render_detections:
                    cv2.rectangle(frame, p1, p2, color, thickness=line_width, lineType=cv2.LINE_AA)
                if cfg.flags.render_labels:
                    label = "{}: {:.4f}".format(self.names[class_id], confidence)
                    cv2.putText(frame, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, line_width)

                processed_boxes.append([x, y, w, h])
                processed_confidence.append(confidence)
                processed_class_id.append(class_id)

        return frame, processed_boxes, processed_confidence, processed_class_id


if __name__ == '__main__':
    inference = Inference()
    source_dir = 'test_data/'
    destination = 'results/'
    os.makedirs(destination, exist_ok=True)
    for file in os.listdir(source_dir):
        if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".bmp"):
            im_path = f'{source_dir}{file}'
            out_path = f'{destination}out_{file}'
            im = cv2.imread(im_path)
            frame_out, boxes_out, _, _ = inference.infer(im)
            cv2.imwrite(out_path, frame_out)
