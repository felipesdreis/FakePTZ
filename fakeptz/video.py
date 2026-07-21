import asyncio
import time
from typing import Callable

import cv2
import numpy as np
import pyvirtualcam

from fakeptz.config import (
    CAPTURE_FPS,
    CAPTURE_HEIGHT,
    CAPTURE_WIDTH,
    MAX_ZOOM,
    MIN_ZOOM,
    MODE_PAN_TILT,
    PAN_TILT_STEP,
    TRANSITION_DURATION_SECONDS,
    ZOOM_STEP,
    CropMode,
    OUTPUT_HEIGHT,
    OUTPUT_WIDTH,
    VIRTUAL_CAM_DEVICE,
    crop_coords_for,
)


def crop_frame(frame: np.ndarray, zoom: float = 1.0, pan: float = 0.5, tilt: float = 0.5) -> np.ndarray:
    height, width = frame.shape[:2]
    h_start, h_end, w_start, w_end = crop_coords_for(width, height, zoom=zoom, pan=pan, tilt=tilt)
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

    # ponytail: aceita qualquer resolução reportada pelo device; só falha se
    # vier 0x0 (device inválido/sem sinal) ou o fps fugir da tolerância.
    if actual_width <= 0 or actual_height <= 0:
        capture.release()
        raise CaptureError(
            f"Dispositivo de captura {camera_index} não reportou uma resolução válida "
            f"(retornou {actual_width}x{actual_height})."
        )

    # ponytail: tolerância de 1fps porque webcams raramente reportam o fps exato solicitado
    if abs(actual_fps - fps) > 1:
        capture.release()
        raise CaptureError(
            f"Dispositivo não suporta {fps}fps "
            f"(retornou {actual_width}x{actual_height}@{actual_fps:.0f}fps, "
            f"solicitado {width}x{height}@{fps}fps)."
        )

    return capture


class VideoPipeline:
    def __init__(self, camera_index: int = 0, clock: Callable[[], float] = time.monotonic):
        self.camera_index = camera_index
        self.mode = CropMode.CENTRO
        self.status = "OFFLINE"
        self.current_fps = 0.0
        self._running = False

        self.zoom, self.pan, self.tilt = 1.0, 0.5, 0.5
        self.zoom_target, self.pan_target, self.tilt_target = 1.0, 0.5, 0.5
        self._clock = clock
        self._transition_start = None
        self._transition_from = (1.0, 0.5, 0.5)

    def set_target(self, *, zoom: float = None, pan: float = None, tilt: float = None) -> None:
        if zoom is not None:
            self.zoom_target = min(max(zoom, MIN_ZOOM), MAX_ZOOM)
        if pan is not None:
            self.pan_target = min(max(pan, 0.0), 1.0)
        if tilt is not None:
            self.tilt_target = min(max(tilt, 0.0), 1.0)
        self._transition_from = (self.zoom, self.pan, self.tilt)
        self._transition_start = self._clock()

    def set_mode(self, mode: CropMode) -> None:
        self.mode = mode
        pan, tilt = MODE_PAN_TILT[mode]
        self.set_target(zoom=1.0, pan=pan, tilt=tilt)

    def nudge_pan(self, direction: int) -> None:
        self.set_target(pan=self.pan_target + direction * PAN_TILT_STEP)

    def nudge_tilt(self, direction: int) -> None:
        self.set_target(tilt=self.tilt_target + direction * PAN_TILT_STEP)

    def nudge_zoom(self, direction: int) -> None:
        self.set_target(zoom=self.zoom_target + direction * ZOOM_STEP)

    def _advance_transition(self) -> None:
        if self._transition_start is None:
            return
        elapsed = self._clock() - self._transition_start
        t = min(elapsed / TRANSITION_DURATION_SECONDS, 1.0)
        zoom_from, pan_from, tilt_from = self._transition_from
        self.zoom = zoom_from + (self.zoom_target - zoom_from) * t
        self.pan = pan_from + (self.pan_target - pan_from) * t
        self.tilt = tilt_from + (self.tilt_target - tilt_from) * t
        if t >= 1.0:
            self._transition_start = None

    def process_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        self._advance_transition()
        cropped = crop_frame(raw_frame, zoom=self.zoom, pan=self.pan, tilt=self.tilt)
        return resize_frame(cropped)

    async def run(self, on_error: Callable[[str], None]) -> None:
        try:
            capture = open_capture(self.camera_index, CAPTURE_WIDTH, CAPTURE_HEIGHT, CAPTURE_FPS)
        except CaptureError as exc:
            self.status = "ERRO"
            on_error(str(exc))
            return

        try:
            camera = pyvirtualcam.Camera(
                width=OUTPUT_WIDTH,
                height=OUTPUT_HEIGHT,
                fps=CAPTURE_FPS,
                device=VIRTUAL_CAM_DEVICE,
            )
        except RuntimeError as exc:
            capture.release()
            self.status = "ERRO"
            on_error(f"Câmera virtual indisponível: {exc}")
            return

        self._running = True
        self.status = "ONLINE"
        frame_count = 0
        fps_window_start = time.monotonic()

        try:
            with camera:
                while self._running:
                    ok, raw_frame = await asyncio.to_thread(capture.read)
                    if not ok:
                        self.status = "ERRO"
                        on_error("Falha ao ler frame do dispositivo de captura.")
                        break

                    output_frame = self.process_frame(raw_frame)
                    output_frame_rgb = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
                    await asyncio.to_thread(camera.send, output_frame_rgb)
                    await asyncio.to_thread(camera.sleep_until_next_frame)

                    frame_count += 1
                    elapsed = time.monotonic() - fps_window_start
                    if elapsed >= 1.0:
                        self.current_fps = frame_count / elapsed
                        frame_count = 0
                        fps_window_start = time.monotonic()
        finally:
            capture.release()
            self._running = False

    def stop(self) -> None:
        self._running = False
