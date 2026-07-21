import numpy as np

from fakeptz.config import MODE_PAN_TILT, CropMode
from fakeptz.video import crop_frame, resize_frame


def _sample_frame():
    return np.arange(1080 * 1920 * 3, dtype=np.uint8).reshape(1080, 1920, 3)


def _sample_frame_720p():
    return np.arange(720 * 1280 * 3, dtype=np.uint8).reshape(720, 1280, 3)


def _pan_tilt(mode):
    return MODE_PAN_TILT[mode]


def test_crop_frame_esquerda_shape_and_slice():
    frame = _sample_frame()
    pan, tilt = _pan_tilt(CropMode.ESQUERDA)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 0:1280])


def test_crop_frame_centro_shape_and_slice():
    frame = _sample_frame()
    pan, tilt = _pan_tilt(CropMode.CENTRO)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 320:1600])


def test_crop_frame_direita_shape_and_slice():
    frame = _sample_frame()
    pan, tilt = _pan_tilt(CropMode.DIREITA)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (720, 1280, 3)
    assert np.array_equal(cropped, frame[180:900, 640:1920])


def test_resize_frame_produces_720p():
    cropped = np.zeros((720, 1280, 3), dtype=np.uint8)
    resized = resize_frame(cropped)
    assert resized.shape == (720, 1280, 3)


def test_crop_frame_esquerda_720p_shape_and_slice():
    frame = _sample_frame_720p()
    pan, tilt = _pan_tilt(CropMode.ESQUERDA)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (480, 853, 3)
    assert np.array_equal(cropped, frame[120:600, 0:853])


def test_crop_frame_centro_720p_shape_and_slice():
    frame = _sample_frame_720p()
    pan, tilt = _pan_tilt(CropMode.CENTRO)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (480, 853, 3)
    assert np.array_equal(cropped, frame[120:600, 214:1067])


def test_crop_frame_direita_720p_shape_and_slice():
    frame = _sample_frame_720p()
    pan, tilt = _pan_tilt(CropMode.DIREITA)
    cropped = crop_frame(frame, pan=pan, tilt=tilt)
    assert cropped.shape == (480, 853, 3)
    assert np.array_equal(cropped, frame[120:600, 427:1280])


def test_crop_frame_zoom_shrinks_crop():
    frame = _sample_frame()
    cropped = crop_frame(frame, zoom=2.0, pan=0.5, tilt=0.5)
    assert cropped.shape == (360, 640, 3)


def test_crop_frame_extreme_pan_tilt_stays_within_frame_bounds():
    frame = _sample_frame()
    top_left = crop_frame(frame, zoom=2.0, pan=0.0, tilt=0.0)
    bottom_right = crop_frame(frame, zoom=2.0, pan=1.0, tilt=1.0)
    assert top_left.shape == bottom_right.shape == (360, 640, 3)
