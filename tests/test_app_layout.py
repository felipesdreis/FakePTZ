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

    def set_mode(self, mode):
        self.mode = mode
        self.set_mode_calls.append(mode)

    def nudge_pan(self, direction):
        self.nudge_pan_calls.append(direction)

    def nudge_tilt(self, direction):
        self.nudge_tilt_calls.append(direction)

    def nudge_zoom(self, direction):
        self.nudge_zoom_calls.append(direction)

    async def run(self, on_error):
        return None


@pytest.mark.asyncio
async def test_app_starts_with_centro_active_and_shows_three_buttons():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test():
        assert app.active_mode == CropMode.CENTRO
        assert app.query_one("#btn-esquerda")
        assert app.query_one("#btn-centro")
        assert app.query_one("#btn-direita")
        assert "active" in app.query_one("#btn-centro").classes
