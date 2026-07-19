import numpy as np

from fakeptz.config import CropMode
from fakeptz.video import VideoPipeline


def test_pipeline_default_mode_is_centro():
    pipeline = VideoPipeline()
    assert pipeline.mode == CropMode.CENTRO


def test_set_mode_changes_active_mode():
    pipeline = VideoPipeline()
    pipeline.set_mode(CropMode.ESQUERDA)
    assert pipeline.mode == CropMode.ESQUERDA


def test_process_frame_applies_crop_and_resize():
    pipeline = VideoPipeline()
    raw_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    output = pipeline.process_frame(raw_frame)

    assert output.shape == (480, 854, 3)
