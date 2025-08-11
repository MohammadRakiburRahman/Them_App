
from easydict import EasyDict as edict

__C = edict()
cfg = __C

__C.detector = edict()
__C.detector.weight_file = "model_data/yolov11m-face.pt"  # yolov8m.pt path(s)
__C.detector.classes = None  # filter by class: --class 0, or --class 0 2 3
__C.detector.OBJECTNESS_CONFIDANCE = 0.2
__C.detector.NMS_THRESHOLD = 0.45
__C.detector.device = 'cpu' #'cpu'  # if GPU give the device ID; EX: , else 'cpu'
__C.detector.verbose = True

__C.general = edict()
__C.general.COLORS = {
                          'green': [64, 255, 64],
                          'blue': [255, 128, 0],
                          'coral': [0, 128, 255],
                          'yellow': [0, 255, 255],
                          'gray': [169, 169, 169],
                          'cyan': [255, 255, 0],
                          'magenta': [255, 0, 255],
                          'white': [255, 255, 255],
                          'red': [64, 0, 255]
                      }

# overlay Flags
__C.flags = edict()
__C.flags.render_detections = False
__C.flags.render_labels = False
