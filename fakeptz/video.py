import cv2
import numpy as np

from fakeptz.config import CROP_COORDS, OUTPUT_HEIGHT, OUTPUT_WIDTH, CropMode


def crop_frame(frame: np.ndarray, mode) -> np.ndarray:
    h_start, h_end, w_start, w_end = CROP_COORDS[mode]
    return frame[h_start:h_end, w_start:w_end]


def resize_frame(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(frame, (OUTPUT_WIDTH, OUTPUT_HEIGHT), interpolation=cv2.INTER_LINEAR)


class CaptureError(Exception):
    pass


def open_capture(camera_index: int, width: int, height: int, fps: int) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise CaptureError(
            f"Não foi possível abrir o dispositivo de captura {camera_index}."
        )

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = capture.get(cv2.CAP_PROP_FPS)

    # ponytail: tolerância de 1fps porque webcams raramente reportam o fps exato solicitado
    if actual_width != width or actual_height != height or abs(actual_fps - fps) > 1:
        capture.release()
        raise CaptureError(
            f"Dispositivo não suporta {width}x{height}@{fps}fps "
            f"(retornou {actual_width}x{actual_height}@{actual_fps:.0f}fps)."
        )

    return capture


class VideoPipeline:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.mode = CropMode.CENTRO
        self.status = "OFFLINE"
        self.current_fps = 0.0
        self._running = False

    def set_mode(self, mode: CropMode) -> None:
        self.mode = mode

    def process_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        cropped = crop_frame(raw_frame, self.mode)
        return resize_frame(cropped)
