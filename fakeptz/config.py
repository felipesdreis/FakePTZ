from enum import Enum
from typing import Tuple


class CropMode(str, Enum):
    ESQUERDA = "ESQUERDA"
    CENTRO = "CENTRO"
    DIREITA = "DIREITA"


CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
CAPTURE_FPS = 30

OUTPUT_WIDTH = CAPTURE_WIDTH * 2 // 3  # 1280 — iguala o crop nativo em zoom 1x, evita downscale desnecessário
OUTPUT_HEIGHT = CAPTURE_HEIGHT * 2 // 3  # 720

VIRTUAL_CAM_DEVICE = "virtual_cam_ptz"

MIN_ZOOM = 1.0
MAX_ZOOM = 3.0
TRANSITION_DURATION_SECONDS = 0.3
PAN_TILT_STEP = 0.05
ZOOM_STEP = 0.2

MODE_PAN_TILT = {
    CropMode.ESQUERDA: (0.0, 0.5),
    CropMode.CENTRO: (0.5, 0.5),
    CropMode.DIREITA: (1.0, 0.5),
}

MACRO_SLOTS = ("M1", "M2", "M3")
DEFAULT_MACRO_POSITION = (0.5, 0.5, 1.0)  # pan, tilt, zoom — mesmo neutro do CENTRO

REMOTE_HTTP_PORT = 8642


def crop_coords_for(
    width: int, height: int, zoom: float = 1.0, pan: float = 0.5, tilt: float = 0.5
) -> Tuple[int, int, int, int]:
    zoom = min(max(zoom, MIN_ZOOM), MAX_ZOOM)
    pan = min(max(pan, 0.0), 1.0)
    tilt = min(max(tilt, 0.0), 1.0)

    crop_h = int(height * 2 / 3 / zoom)
    crop_w = int(width * 2 / 3 / zoom)
    max_h_start = height - crop_h
    max_w_start = width - crop_w
    h_start = round(tilt * max_h_start)
    w_start = round(pan * max_w_start)
    return h_start, h_start + crop_h, w_start, w_start + crop_w


CROP_COORDS = {
    mode: crop_coords_for(CAPTURE_WIDTH, CAPTURE_HEIGHT, pan=pan, tilt=tilt)
    for mode, (pan, tilt) in MODE_PAN_TILT.items()
}
