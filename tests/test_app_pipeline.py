from unittest.mock import patch

import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode


class FakePipeline:
    def __init__(self):
        self.mode = CropMode.CENTRO
        self.status = "ONLINE"
        self.current_fps = 30.0
        self.zoom, self.pan, self.tilt = 1.0, 0.5, 0.5
        self.set_mode_calls = []
        self.nudge_pan_calls = []
        self.nudge_tilt_calls = []
        self.nudge_zoom_calls = []
        self.set_target_calls = []

    def set_mode(self, mode):
        self.mode = mode
        self.set_mode_calls.append(mode)

    def set_target(self, *, zoom=None, pan=None, tilt=None):
        self.set_target_calls.append({"zoom": zoom, "pan": pan, "tilt": tilt})
        if zoom is not None:
            self.zoom = zoom
        if pan is not None:
            self.pan = pan
        if tilt is not None:
            self.tilt = tilt

    def nudge_pan(self, direction):
        self.nudge_pan_calls.append(direction)

    def nudge_tilt(self, direction):
        self.nudge_tilt_calls.append(direction)

    def nudge_zoom(self, direction):
        self.nudge_zoom_calls.append(direction)

    async def run(self, on_error):
        return None


@pytest.mark.asyncio
async def test_mode_switch_forwards_to_pipeline():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert pipeline.set_mode_calls == [CropMode.DIREITA]


@pytest.mark.asyncio
async def test_status_panel_shows_pipeline_telemetry():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test():
        status_panel = app.query_one("#status-panel")
        rendered = str(status_panel.content)
        assert "ONLINE" in rendered
        assert "30 FPS" in rendered


@pytest.mark.asyncio
async def test_status_panel_shows_zoom_pan_tilt():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test():
        status_panel = app.query_one("#status-panel")
        rendered = str(status_panel.content)
        assert "1.0x" in rendered
        assert "50%" in rendered


@pytest.mark.asyncio
async def test_pipeline_error_triggers_safe_exit():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test():
        with patch.object(app, "exit") as mock_exit:
            app._handle_pipeline_error("driver ausente")
            mock_exit.assert_called_once_with(message="[ERRO] driver ausente")
