import numpy as np

from fakeptz.config import CropMode
from fakeptz.video import crop_frame, resize_frame


def _sample_frame():
    return np.arange(1080 * 1920 * 3, dtype=np.uint8).reshape(1080, 1920, 3)


def test_crop_frame_esquerda_shape_and_slice():
    frame = _sample_frame()
    cropped = crop_frame(frame, CropMode.ESQUERDA)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 0:1280])


def test_crop_frame_centro_shape_and_slice():
    frame = _sample_frame()
    cropped = crop_frame(frame, CropMode.CENTRO)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 320:1600])


def test_crop_frame_direita_shape_and_slice():
    frame = _sample_frame()
    cropped = crop_frame(frame, CropMode.DIREITA)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 640:1920])


def test_resize_frame_produces_480p():
    cropped = np.zeros((720, 1280, 3), dtype=np.uint8)
    resized = resize_frame(cropped)
    assert resized.shape == (480, 854, 3)
