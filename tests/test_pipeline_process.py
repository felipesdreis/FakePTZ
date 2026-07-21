import numpy as np

from fakeptz.config import MODE_PAN_TILT, MAX_ZOOM, MIN_ZOOM, TRANSITION_DURATION_SECONDS, CropMode
from fakeptz.video import VideoPipeline


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_pipeline_default_mode_is_centro():
    pipeline = VideoPipeline()
    assert pipeline.mode == CropMode.CENTRO


def test_pipeline_default_zoom_pan_tilt():
    pipeline = VideoPipeline()
    assert pipeline.zoom == 1.0
    assert pipeline.pan == 0.5
    assert pipeline.tilt == 0.5


def test_set_mode_changes_active_mode():
    pipeline = VideoPipeline()
    pipeline.set_mode(CropMode.ESQUERDA)
    assert pipeline.mode == CropMode.ESQUERDA


def test_process_frame_applies_crop_and_resize():
    pipeline = VideoPipeline()
    raw_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    output = pipeline.process_frame(raw_frame)

    assert output.shape == (720, 1280, 3)


def test_set_target_does_not_apply_instantly():
    clock = FakeClock()
    pipeline = VideoPipeline(clock=clock)

    pipeline.set_target(pan=1.0)

    assert pipeline.pan_target == 1.0
    assert pipeline.pan == 0.5


def test_transition_advances_toward_target_over_time():
    clock = FakeClock()
    pipeline = VideoPipeline(clock=clock)
    raw_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    pipeline.set_target(pan=1.0)
    clock.advance(TRANSITION_DURATION_SECONDS / 2)
    pipeline.process_frame(raw_frame)

    assert 0.5 < pipeline.pan < 1.0


def test_transition_completes_exactly_at_target_after_full_duration():
    clock = FakeClock()
    pipeline = VideoPipeline(clock=clock)
    raw_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    pipeline.set_target(pan=1.0)
    clock.advance(TRANSITION_DURATION_SECONDS)
    pipeline.process_frame(raw_frame)

    assert pipeline.pan == 1.0


def test_set_mode_targets_the_preset_pan_and_tilt():
    clock = FakeClock()
    pipeline = VideoPipeline(clock=clock)

    pipeline.set_mode(CropMode.DIREITA)

    expected_pan, expected_tilt = MODE_PAN_TILT[CropMode.DIREITA]
    assert pipeline.pan_target == expected_pan
    assert pipeline.tilt_target == expected_tilt
    assert pipeline.zoom_target == 1.0


def test_nudge_pan_moves_target_and_clamps_at_bounds():
    pipeline = VideoPipeline()

    for _ in range(100):
        pipeline.nudge_pan(-1)
    assert pipeline.pan_target == 0.0

    for _ in range(100):
        pipeline.nudge_pan(1)
    assert pipeline.pan_target == 1.0


def test_nudge_tilt_moves_target_and_clamps_at_bounds():
    pipeline = VideoPipeline()

    for _ in range(100):
        pipeline.nudge_tilt(-1)
    assert pipeline.tilt_target == 0.0

    for _ in range(100):
        pipeline.nudge_tilt(1)
    assert pipeline.tilt_target == 1.0


def test_nudge_zoom_moves_target_and_clamps_at_bounds():
    pipeline = VideoPipeline()

    for _ in range(100):
        pipeline.nudge_zoom(-1)
    assert pipeline.zoom_target == MIN_ZOOM

    for _ in range(100):
        pipeline.nudge_zoom(1)
    assert pipeline.zoom_target == MAX_ZOOM
