import cv2
import numpy as np

from fakeptz.config import CROP_COORDS, OUTPUT_HEIGHT, OUTPUT_WIDTH


def crop_frame(frame: np.ndarray, mode) -> np.ndarray:
    h_start, h_end, w_start, w_end = CROP_COORDS[mode]
    return frame[h_start:h_end, w_start:w_end]


def resize_frame(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(frame, (OUTPUT_WIDTH, OUTPUT_HEIGHT), interpolation=cv2.INTER_LINEAR)
